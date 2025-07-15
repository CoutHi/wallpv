import cv2
from gi.repository import Gtk, Gdk, GdkPixbuf
from enum import Enum
import sys
import os
import configparser
import xdg.BaseDirectory
import subprocess
import mimetypes
import gi
gi.require_version("Gtk", "4.0")


class ErrorId(Enum):
    PERSISTENCE = 1
    CONFIG_EMPTY = 2
    FFMPEG = 3
    CACHE_NO_PERMS = 4
    CACHE_EXCEPTION = 5
    MPVPAPER = 6
    WRONG_CONFIG_FOLDER = 7


WIDTH = 1408
HEIGHT = 792

css = b"""
    button.thumbnail {
        padding: 0;
        border: none;
        min-width: 0;
        min-height: 0;
    }
"""

provider = Gtk.CssProvider()
provider.load_from_data(css)
Gtk.StyleContext.add_provider_for_display(
    Gdk.Display.get_default(),
    provider,
    Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
)


def on_activate(app):

    win = Gtk.ApplicationWindow(application=app)
    print("WINDOW MADE")

    # cache path should be /home/user/.cache/wallpv
    cache_path = os.path.join(xdg.BaseDirectory.xdg_cache_home, "wallpv")
    print("CACHE PATH: ", cache_path)

    try:
        os.mkdir(cache_path)
    except FileExistsError:
        print("Cache directory exists, continuing normally.\n")
    except PermissionError:
        raise_ui_error(ErrorId.CACHE_NO_PERMS,
                       "YOU DONT HAVE THE PERMISSIONS TO CREATE THE CACHE DIRECTORY IN " + cache_path)
    except Exception:
        raise_ui_error(ErrorId.CACHE_EXCEPTION,
                       "EXCEPTION WHILE CREATING CACHE IN " + cache_path)

    # Read the config for the folder to check for gifs
    img_folder, err, config_file = read_conf(win)
    if err:
        raise_ui_error(ErrorId.CONFIG_EMPTY, win,
                       "YOU DONT HAVE A CONFIG FILE " + "(" + config_file + ")")
    print("IMAGE FOLDER: " + img_folder + "\n")

    # an array for storing the names of files found in the folder
    wallpaper_files = []

    prepared_files = []

    # Check if the wallpaper folder in the config is correct
    try:
        os.listdir(img_folder)
    except FileNotFoundError as e:
        raise_ui_error(ErrorId.WRONG_CONFIG_FOLDER, win,
                       "WALLPAPER FOLDER IS INCORRECT\n" + str(e) + "\nERROR CODE " + str(e.errno))

    # check the mimetype of files in the wallpaper folder and append them to the list if they're either a video or an image file
    for file in os.listdir(img_folder):
        mimetype, _ = mimetypes.guess_file_type(file)
        if mimetype:
            type_name, _ = str(mimetype).split('/', 1)
            if type_name == "image" or type_name == "video":
                wallpaper_files.append(file)

    # create thumbnails from the gifs/videos we found so we can display them in the UI
    for file in wallpaper_files:

        mimetype_first_part, _ = mimetypes.guess_file_type(
            file)

        if "video" in mimetype_first_part or mimetypes.guess_file_type(file)[0] == "image/gif":
            print("FILE IS ANIMATED: " + file +
                  " A THUMBNAIL WILL BE GENERATED")

            res, err = create_thumbnails(win, file, cache_path)
            if err is None:
                prepared_files.append(res)
            elif err is ErrorId.FFMPEG:
                raise_ui_error(
                    err, win, "FFMPEG RAN INTO AN ISSUE WHILE CREATING THUMBNAILS")
        else:
            prepared_files.append(os.path.join(img_folder, file))

    # Start setting up the UI
    grid = Gtk.Grid.new()
    grid.set_row_spacing(0)
    grid.set_column_spacing(0)
    grid.set_margin_bottom(4)
    grid.set_margin_top(4)
    grid.set_margin_start(4)
    grid.set_margin_end(4)
    grid.set_column_homogeneous(True)

    row = 0
    column = 0
    i = 0
    columns_per_row = 4

    print("\n")
    # a loop to fill the grid with the thumbnails we made, put into buttons
    while i < len(prepared_files):
        if column == columns_per_row:
            column = 0
            row += 1

        # Here we get the name of the file to check against the cache in order to
        # see if it was a gif/video, if it isn't in the cache than it's a normal image
        file_name = os.path.basename(prepared_files[i])

        # This will be used to set the wallpaper path
        path_to_wallpaper: str

        if os.path.isfile(os.path.join(cache_path, file_name)):

            image = Gtk.Image(file=prepared_files[i])
            for file in wallpaper_files:
                file, extension = file.rsplit('.', 1)
                if file.__contains__(file_name.removesuffix(".jpg")):
                    path_to_wallpaper = os.path.join(
                        img_folder, file + "." + extension)

                    resolution = cv2.VideoCapture(path_to_wallpaper)
                    resolutionX = int(resolution.get(cv2.CAP_PROP_FRAME_WIDTH))
                    resolutionY = int(resolution.get(
                        cv2.CAP_PROP_FRAME_HEIGHT))

            image.set_pixel_size(int(WIDTH/columns_per_row - 8))
            filetype = prepared_files[i].rsplit('/', 1)
            file_name = filetype[1].removesuffix(".jpg")
            if file_name + ".gif" in wallpaper_files:
                filetype = "gif"
            else:
                filetype = "video"

        else:
            path_to_wallpaper = os.path.join(img_folder, file_name)
            filetype = "image"
            # Here we're working with pixel buffers to force the 1:1
            # aspect ratio, since we don't have ffmpegthumbnailer for normal images
            try:
                pixel_buffer = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                    path_to_wallpaper, WIDTH/4, WIDTH/4, False)
                image = Gtk.Image.new_from_pixbuf(pixel_buffer)
            except Exception:
                print("FAILED LOADING IMAGE " + path_to_wallpaper)
                i += 1
                continue

            resolution = cv2.imread(path_to_wallpaper)
            resolutionX = int(resolution.shape[1])
            resolutionY = int(resolution.shape[0])

        image.add_css_class("image")

        info_label = Gtk.Label(
            justify=Gtk.Justification.CENTER)
        info_label.set_text(
            filetype + " [" + str(resolutionX) + "x" + str(resolutionY) + "]")

        info_label.set_margin_bottom(4)
        info_label.set_margin_top(4)

        button = Gtk.Button.new()
        button.set_hexpand(False)
        button.set_vexpand(False)

        button.set_margin_bottom(0)
        button.set_margin_end(0)
        button.set_margin_start(0)
        button.set_margin_top(0)

        image.set_pixel_size(WIDTH/4)

        # simple css class to get rid of button's padding and stuff
        button.add_css_class("thumbnail")

        button.connect('clicked', set_wallpaper, win,
                       path_to_wallpaper)

        button.set_child(image)

        # This grid will contain the image, the button and the filetype label
        display_grid = Gtk.Grid()
        display_grid.attach(button, 0, 0, 1, 1)
        display_grid.attach(info_label, 0, 1, 1, 1)

        grid.attach(display_grid, column, row, 1, 1)

        column += 1
        i += 1

    # we create a scrollable window to put the grid into
    scrolled = Gtk.ScrolledWindow.new()
    scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

    # expand grid to edges
    grid.set_hexpand(True)
    grid.set_vexpand(True)

    scrolled.set_child(grid)

    # set window to not be resizable
    win.set_default_size(WIDTH, HEIGHT)
    win.set_resizable(False)

    win.set_child(scrolled)
    win.present()


def read_conf(win) -> tuple[str, ErrorId | None, str]:

    # the config file should be /home/user/.config/wallpv/wallpv.ini
    config_file = os.path.join(
        xdg.BaseDirectory.xdg_config_home, "wallpv", "wallpv.ini")

    config = configparser.ConfigParser()
    config.read(config_file)

    # look under header [Path] for the key folder =
    path_conf = config['Path']
    img_folder = path_conf['folder']

    if img_folder is None or img_folder == "":
        return [None, ErrorId.CONFIG_EMPTY, config_file]

    return [img_folder, None, None]


def create_thumbnails(win, file_to_convert, cache_path) -> tuple[str, ErrorId | None]:
    # remove the file extension
    filename, _ = file_to_convert.rsplit('.', 1)

    file_path = cache_path + "/" + filename + ".jpg"

    # Generate Thumbnails with ffmpegthumbnailer -- Skip if the thumbnail already exists
    if not os.path.isfile(file_path):
        result = subprocess.run(["ffmpegthumbnailer", "-i", file_to_convert,
                                "-s", str(WIDTH/4), "-c", "jpeg", "-a",  "-q", "5", "-o", file_path],   check=True)
        print("FFMPEGTHUMBNAILER EXITED WITH: " + str(result.returncode))

        if result.returncode != 0:
            print("ERROR WITH FFMPEGTHUMBNAILER " + result.stderr.decode())
            return [None, ErrorId.FFMPEG]
    else:
        print("THUMBNAIL ALREADY EXISTS: " + str(file_path))
        return [file_path, None]

    return tuple[file_path, None]


def set_wallpaper(caller, win, file):

    config_dir = os.path.join(xdg.BaseDirectory.xdg_config_home, "wallpv")

    # the user can use the persistence_file, which has the full path to the chosen wallpaper in their window manager config to set the wallpaper at start-up, so their choice
    # is persistent across reboots

    print("FUNCTION SET_WALLPAPER() GOT FILE : " + str(file))
    file_string = str(file)
    file_string = file_string.removesuffix(".jpg")

    bare_file = os.path.basename(file_string)
    print("BARE FILE NAME :" + bare_file)

    print("FULL PATH TO FILE: " + file)

    subprocess.run(["pkill", "mpvpaper"])

    cmd = "mpvpaper ALL -f -o \"loop no-audio\"" + " " + file
    print("COMMAND: " + cmd)
    try:
        result = subprocess.run(
            cmd, check=True, shell=True)
    except ChildProcessError:
        print("ERROR RUNNING MPVPAPER!\nCODE: " + str(result.returncode))
        raise_ui_error(ErrorId.MPVPAPER, win,
                       "ERROR RUNNING MPVPAPER!\nCODE: " + str(result.returncode))

    try:
        persistence_file = open(os.path.join(config_dir, "wallpaper.txt"), "w")
        persistence_file.write(file)
        persistence_file.close()
    except Exception as e:
        print("ERROR OPENING WALLPAPER PERSISTENCE FILE: " + str(e))
        e = "ERROR OPENING WALLPAPER PERSISTENCE FILE\n" + str(e)
        raise_ui_error(ErrorId.PERSISTENCE, win, e)


# I haven't figured out how to call these yet
def hover_button(caller, img):
    img.set_pixel_size(512)


def hover_button_leave(caller, img, columns):
    img.set_pixel_size(int(WIDTH/columns))


def raise_ui_error(error_id, win: Gtk.ApplicationWindow, err):

    print("ENTERING RAISE_UI_ERROR()")

    alert = Gtk.Window(application=win.get_application(),
                       transient_for=win, modal=True, title="Error")

    viewbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,
                      spacing=48, hexpand=True, vexpand=True)

    err_text = Gtk.Label(hexpand=True, vexpand=False, margin_top=24)

    err_text.set_markup("<b>An Error Occured</b>")

    err_text.set_halign(Gtk.Align.CENTER)

    info_text = Gtk.TextView(editable=False, indent=12,
                             monospace=True, can_target=False,
                             hexpand=True, vexpand=True,
                             margin_end=36, margin_start=36,
                             justification=Gtk.Justification.CENTER,
                             pixels_above_lines=12, cursor_visible=False)

    err_buffer = Gtk.TextBuffer(text=str(err))

    info_text.set_buffer(err_buffer)

    exit_btn = Gtk.Button.new_with_label("OK")

    def on_close(caller):
        if ErrorId.FFMPEG or ErrorId.CONFIG_EMPTY or ErrorId.CACHE_NO_PERMS or ErrorId.CACHE_EXCEPTION or ErrorId.MPVPAPER:
            alert.close()
            win.get_application().quit()
            sys.exit(1)
        else:
            return

    exit_btn.connect('clicked', on_close)

    viewbox.append(err_text)
    viewbox.append(info_text)
    viewbox.append(exit_btn)

    alert.set_default_size(1024, 512)
    alert.set_resizable(False)

    alert.set_child(viewbox)

    alert.present()


if __name__ == '__main__':
    app = Gtk.Application(application_id='dev.couthi.wallpv')
    app.connect('activate', on_activate)
    print("CONNECTED APP TO ON_ACTIVATE")
    try:
        print("TRYING APP.RUN")
        sys.exit(app.run(sys.argv))
        print("APP.RUN DONE")
    except Exception as e:
        print(e)
        sys.exit(1)
