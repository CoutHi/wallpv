from enum import Enum
import sys
import argparse
import os
import configparser
import xdg.BaseDirectory
import subprocess
from gi.repository import Gtk, GdkPixbuf, Gdk
import gi
gi.require_version("Gtk", "4.0")


class ErrorId(Enum):
    PERSISTENCE = 1
    CONFIG_EMPTY = 2
    FFMPEG = 3


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

    grid = Gtk.Grid.new()
    grid.set_row_spacing(0)
    grid.set_column_spacing(0)
    grid.set_margin_bottom(4)
    grid.set_margin_top(4)
    grid.set_margin_start(4)
    grid.set_margin_end(4)
    grid.set_column_homogeneous(True)

    # Read the config for the folder to check for gifs
    img_folder = read_conf(win)
    print("IMAGE FOLDER: " + img_folder)

    # an array for storing the names of gif files found in the folder
    gif_files = []

    # find and append gif files in the img_folder
    for file in os.listdir(img_folder):
        if file.endswith(".gif") or file.endswith(".mp4"):
            gif_files.append(file)

    # create thumbnails from the gifs we found so we can display them in the UI
    cached_files, err = create_thumbnails(win, img_folder, gif_files)

    row = 0
    column = 0
    i = 0
    columns_per_row = 4

    # a loop to fill the grid with the thumbnails we made, put into buttons
    while i < len(cached_files):
        if column == columns_per_row:
            column = 0
            row += 1

        image = Gtk.Image.new_from_file(cached_files[i])

        image.set_pixel_size(int(WIDTH/columns_per_row - 8))

        image.get_style_context().add_class("image")

        button = Gtk.Button.new()
        button.set_hexpand(False)
        button.set_vexpand(False)

        button.set_margin_bottom(0)
        button.set_margin_end(0)
        button.set_margin_start(0)
        button.set_margin_top(0)

        # simple css to get rid of button's padding and stuff
        button.get_style_context().add_class("thumbnail")

        button.connect('clicked', set_wallpaper, win,
                       cached_files[i], img_folder)

        button.set_child(image)

        grid.attach(button, column, row, 1, 1)

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


def read_conf(win) -> str:

    # the config file should be /home/user/.config/wallpv/wallpv.ini
    config_file = os.path.join(
        xdg.BaseDirectory.xdg_config_home, "wallpv", "wallpv.ini")

    config = configparser.ConfigParser()
    config.read(config_file)

    # look under header [Path] for the key folder =
    path_conf = config['Path']
    img_folder = path_conf['folder']

    if img_folder is None or img_folder == "":
        raise_ui_error(ErrorId.CONFIG_EMPTY, win,
                       "CONFIG ERROR\nConfig Is Empty")

    return img_folder


def create_thumbnails(win, gif_path, gifs) -> tuple[list[str], str | None]:

    # cache path should be /home/user/.cache/wallpv
    cache_path = os.path.join(xdg.BaseDirectory.xdg_cache_home, "wallpv")
    print("CACHE PATH: ", cache_path)

    try:
        os.mkdir(cache_path)
    except FileExistsError:
        print("Cache directory exists, continuing normally.")
    except PermissionError:
        err_msg = "You Don't Have The Permissions Necessary To Create" + cache_path + "!"
        return [], err_msg
    except Exception as e:
        err_msg = "Exception Occured! " + e
        return [], err_msg

    # a string array for storing the path of cached files
    cache_files = []

    for gif in gifs:
        if gif.endswith(".gif"):
            filename = gif.removesuffix(".gif")
        else:
            filename = gif.removesuffix(".mp4")
        file_path = cache_path + "/" + filename + ".jpg"
        gif_path_full = os.path.join(gif_path, gif)
#        Image.open(os.path.join(gif_path, gif)).convert('RGB').save(filename)

        # Generate Thumbnails with ffmpegthumbnailer -- Skip if the thumbnail already exists
        if not os.path.isfile(file_path):
            result = subprocess.run(["ffmpegthumbnailer", "-i", gif_path_full,
                                    "-s", str(WIDTH/4), "-c", "jpeg", "-a",  "-q", "5", "-o", file_path],   check=True)
            print("FFMPEGTHUMBNAILER EXITED WITH: " + str(result.returncode))

            if result.returncode != 0:
                print("ERROR WITH FFMPEGTHUMBNAILER " + result.stderr.decode())
                raise_ui_error(
                    ErrorId.FFMPEG, win, "ERROR WITH FFMPEGTHUMBNAILER\n" + result.stderr.decode())
        else:
            print("THUMBNAIL ALREADY EXISTS: " + str(file_path))

        cache_files.append(file_path)

    # now we return an array of strings that contain individual paths to our generated thumbnails
    return cache_files, None


def set_wallpaper(caller, win, file, gif_folder):

    config_dir = os.path.join(xdg.BaseDirectory.xdg_config_home, "wallpv")

    # the user can use the persistence_file, which has the full path to the chosen wallpaper in their window manager config to set the wallpaper at start-up, so their choice
    # is persistent across reboots

    print("FUNCTION SET_WALLPAPER() GOT FILE : " + str(file))
    file_string = str(file)
    file_string = file_string.removesuffix(".jpg")

    bare_file = os.path.basename(file_string)
    print("BARE FILE NAME :" + bare_file)

    full_path = os.path.join(gif_folder, bare_file)

    if os.path.isfile(full_path + ".gif"):
        full_path = full_path + ".gif"
    elif os.path.isfile(full_path + ".mp4"):
        full_path = full_path + ".mp4"
    else:
        print("FILE COULD NOT BE FOUND!")
        exit(1)

    print("FULL PATH TO FILE: " + full_path)

    subprocess.run(["pkill", "mpvpaper"])

    cmd = "mpvpaper ALL -f -o \"loop no-audio\"" + " " + full_path
    print("COMMAND: " + cmd)
    try:
        result = subprocess.run(
            cmd, check=True, shell=True)
    except ChildProcessError:
        print("ERROR RUNNING MPVPAPER!\nCODE: " + str(result.returncode))

    try:
        persistence_file = open(os.path.join(config_dir, "wallpaper.txt"), "w")
        persistence_file.write(full_path)
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
        if ErrorId.FFMPEG or ErrorId.CONFIG_EMPTY:
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


app = Gtk.Application(application_id='dev.couthi.wallpv')
app.connect('activate', on_activate)
app.run(sys.argv)
