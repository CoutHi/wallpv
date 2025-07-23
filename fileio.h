#ifndef FILEIO_H

#define FILEIO_H

#endif // !FILEIO_H

#define WALLPAPER_FILE "wallpapers.txt"
#define MAX_WALLPAPERS 1024
#define CACHE_FILE "cachefiles.txt"

struct CallbackData {
  int index;
  struct FolderData *data;
};

struct FolderData {
  char **files;
  char **cache_files;
  int count;
};

struct FolderData get_wallpapers(char *path);

void generate_thumbnails(struct FolderData data);

int run_python(char *cmd);

char *read_conf(char *config);

int write_wallpaper(char *path);
