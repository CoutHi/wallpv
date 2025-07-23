#include "fileio.h"
#include <gdk-pixbuf/gdk-pixbuf.h>
#include <gdk/gdk.h>
#include <gio/gio.h>
#include <glib-object.h>
#include <glib.h>
#include <gtk/gtk.h>
#include <gtk/gtkshortcut.h>
#include <stdio.h>

#define WIDTH 1408
#define COLUMNS 4

static struct FolderData g_data;

static void on_image_chosen(GtkGestureClick *gesture, gint n_press, gdouble x,
                            gdouble y, gpointer index) {

  //  struct CallbackData *cd = g_new(struct CallbackData, 1);
  //  cd = index;
  printf("CHOSE: %s\n", g_data.files[GPOINTER_TO_INT(index)]);

  char *cmd = malloc(1024);
  int len;
  int status;

  len = snprintf(cmd, 1023, "pkill mpvpaper");
  if (len > 1023) {
    printf("CMD BUFFER WASN'T ENOUGH TO KILL MPVPAPER!\n");
    exit(1);
  }
  printf("KILLING MPVPAPER\n");
  cmd[len + 1] = '\0';
  status = system(cmd);
  if (status != 0) {
    printf("ERROR KILLING MPVPAPER!\n");
    exit(1);
  }

  len = snprintf(cmd, 1023, "mpvpaper ALL -f -o \"loop no-audio\" %s",
                 g_data.files[GPOINTER_TO_INT(index)]);
  if (len > 1023) {
    printf("CMD BUFFER WASN'T ENOUGH TO KILL MPVPAPER!\n");
    exit(1);
  }
  cmd[len + 1] = '\0';
  printf("SETTING WALLPAPER\n");
  status = system(cmd);
  printf("GOT: %d\n", status);
  if (status != 0) {
    exit(1);
  }

  write_wallpaper(g_data.files[GPOINTER_TO_INT(index)]);
  free(cmd);
}

void display_thumbs(struct FolderData data, GtkWidget *win) {
  GtkWidget *grid = gtk_grid_new();
  gtk_grid_set_column_homogeneous(GTK_GRID(grid), TRUE);

  GtkWidget *scrollable = gtk_scrolled_window_new();

  int i = 0;
  int y = 0;
  int x = 0;
  while (i < data.count) {

    struct CallbackData *cd = g_new(struct CallbackData, 1);
    cd->data = &data;
    cd->index = i;

    GtkGesture *click = gtk_gesture_click_new();
    gtk_gesture_single_set_button(GTK_GESTURE_SINGLE(click),
                                  GDK_BUTTON_PRIMARY);

    GtkWidget *img = gtk_image_new_from_file(data.cache_files[i]);
    gtk_image_set_pixel_size(GTK_IMAGE(img), WIDTH / COLUMNS);

    gtk_widget_add_controller(GTK_WIDGET(img), GTK_EVENT_CONTROLLER(click));
    g_signal_connect(click, "pressed", G_CALLBACK(on_image_chosen),
                     GINT_TO_POINTER(i));

    gtk_grid_attach(GTK_GRID(grid), GTK_WIDGET(img), y, x, 1, 1);

    if (y == COLUMNS - 1) {
      y = 0;
      x++;
    } else {
      y++;
    }
    i++;
  }

  gtk_scrolled_window_set_child(GTK_SCROLLED_WINDOW(scrollable),
                                GTK_WIDGET(grid));
  gtk_window_set_child(GTK_WINDOW(win), GTK_WIDGET(scrollable));
}

static void activate(GtkApplication *app, gpointer appdata) {

  struct FolderData data;

  const char *config_path = g_get_user_config_dir();

  char *config_path_full =
      g_build_filename(config_path, "wallpv", "wallpv.conf", NULL);

  char *wallpaper_dir = read_conf(config_path_full);

  printf("RUNNING GET_WALLPAPERS WITH %s\n", wallpaper_dir);
  data = get_wallpapers(wallpaper_dir);

  g_data = data;

  g_free(config_path_full);
  free(wallpaper_dir);

  generate_thumbnails(data);

  printf("TOTAL FILES: %d\n", data.count);

  GtkWidget *win = gtk_application_window_new(app);

  gtk_window_set_title(GTK_WINDOW(win), "Wallpv");
  gtk_window_set_resizable(GTK_WINDOW(win), 0);
  gtk_window_set_default_size(GTK_WINDOW(win), WIDTH, 792);

  time_t start = time(NULL);

  display_thumbs(data, GTK_WIDGET(win));

  time_t end = time(NULL);
  printf("SETTING UP THE UI TOOK: %ld\n", end - start);

  gtk_window_present(GTK_WINDOW(win));
}

int main(int argc, char **argv) {

  GtkApplication *app;
  int status = 0;

  app = gtk_application_new("dev.couthi.wallpv", G_APPLICATION_DEFAULT_FLAGS);
  g_signal_connect(app, "activate", G_CALLBACK(activate), argv);
  status = g_application_run(G_APPLICATION(app), argc, argv);

  g_object_unref(app);

  return 0;
}
