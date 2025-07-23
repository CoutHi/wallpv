#include "fileio.h"
#include <gio/gio.h>
#include <glib.h>
#include <gtk/gtk.h>
#include <gtk/gtkshortcut.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

struct FolderData get_wallpapers(char *path) {
  struct FolderData data;

  data.files = malloc(sizeof(char *) * MAX_WALLPAPERS);
  data.cache_files = malloc(sizeof(char *) * MAX_WALLPAPERS);

  if (!data.files || !data.cache_files) {
    perror("malloc");
    exit(1);
  }

  const char *cache_dir = g_get_user_cache_dir();

  char *cache_dir_full = g_build_filename(cache_dir, "wallpv", NULL);

  char cwd[1024];
  size_t len = sizeof(cwd);

  // Get the current working dir
  int bytes = MIN(readlink("/proc/self/exe", cwd, len), len - 1);
  if (bytes >= 0) {
    cwd[bytes] = '\0';
  }
  for (int z = bytes - 1; z > 0; z--) {
    if (cwd[z] == '/') {
      cwd[z] = '\0';
      printf("CWD: %s\n", cwd);
      break;
    }
  }

  char *python_path = g_build_filename(cwd, "fileinfo.py", NULL);

  int needed =
      snprintf(NULL, 0, "python3 %s %s %s", python_path, path, cache_dir_full);
  char *cmd = malloc(needed + 1);
  int ret = snprintf(cmd, 8192, "python3 %s %s %s", python_path, path,
                     cache_dir_full);
  if (ret < 0 || ret > 8192) {
    printf("SNPRINTF TRUNCATED OR FAILED\n");
  }
  printf("PYTHON CMD: %s", cmd);
  printf("\n");

  int status = 0;
  status = run_python(cmd);
  printf("PYTHON EXITED WITH %d\n", status);

  char *wallpaper_file = g_build_filename(cwd, "wallpapers.txt", NULL);
  printf("WALLPAPER FILE: %s\n", wallpaper_file);
  char *cache_file = g_build_filename(cwd, "cachefiles.txt", NULL);
  printf("CACHE FILE: %s\n", cache_file);

  FILE *f;
  f = fopen(wallpaper_file, "r");
  if (!f) {
    printf("FAILED TO OPEN THE FILE %s\n", wallpaper_file);
    exit(1);
  }

  char buffer[2048];

  int i = 0;
  while (fgets(buffer, 2048, f) != NULL) {

    buffer[strcspn(buffer, "\r\n")] = '\0';

    data.files[i] = strdup(buffer);
    i++;
  }

  data.count = i;

  printf("\nWALLPAPER FILES\n");
  for (int tmp = 0; tmp < i; tmp++) {
    printf("%s\n", data.files[tmp]);
  }

  fclose(f);

  f = fopen(cache_file, "r");
  if (!f) {
    perror("FAILED TO OPEN CACHE TEXT FILE");
    exit(1);
  }

  i = 0;
  while (fgets(buffer, 2048, f) != NULL) {

    buffer[strcspn(buffer, "\r\n")] = '\0';

    data.cache_files[i] = strdup(buffer);
    i++;
  }
  fclose(f);

  printf("\nCACHE FILES\n");
  for (int tmp = 0; tmp < i; tmp++) {
    printf("%s\n", data.cache_files[tmp]);
  }

  return data;
}

void generate_thumbnails(struct FolderData data) {

  int i = 0;
  int max = data.count;

  int needed =
      snprintf(NULL, 0, "ffmpegthumbnailer -i %s -s 256 -q 3 -c jpeg -o %s",
               data.files[i], data.cache_files[i]);

  char *cmd = malloc(needed + 1024);

  time_t start, end;
  start = time(NULL);
  while (i < data.count) {
    // Check if the thumbnail already exists, skip if it does
    gboolean status = FALSE;
    GFile *file = g_file_new_for_path(data.cache_files[i]);
    status = g_file_query_exists(file, NULL);
    g_free(file);
    printf("CHECKED FILE %s GOT STATUS %d\n", data.cache_files[i], status);
    if (status == TRUE) {
      i++;
      continue;
    }

    snprintf(cmd, needed + 1024,
             "ffmpegthumbnailer -i \"%s\" -s 1024 -a -c png -o \"%s\"",
             data.files[i], data.cache_files[i]);

    printf("RUNNING FFMPEGTHUMBNAILER WITH %s\n", cmd);

    status = system(cmd);

    if (status != 0) {
      printf("FFMPEG STATUS %d\n", status);
    }
    i++;
  }
  end = time(NULL);

  double time_taken = end - start;
  printf("CHECKING FILES TOOK: %lf\n", time_taken);
}

int run_python(char *cmd) {
  int status = 0;

  status = system(cmd);

  return status;
}

char *read_conf(char *config) {
  FILE *f;
  f = fopen(config, "r");
  if (!f) {
    perror("COULDN'T OPEN THE CONFIG!\n");
    exit(1);
  }

  char *path = malloc(2048);

  if (!fgets(path, 2048, f)) {
    perror("fgets");
    exit(1);
  }

  path[strcspn(path, "\r\n")] = '\0';

  printf("PATH FROM CONFIG: %s\n", path);

  fclose(f);

  return path;
}

int write_wallpaper(char *path) {
  const char *config_path = g_get_user_config_dir();

  char *wallpaper_file =
      g_build_filename(config_path, "wallpv", "wallpaper.txt", NULL);

  printf("WRITING TO %s\n", wallpaper_file);

  FILE *f;
  f = fopen(wallpaper_file, "w");
  if (!f) {
    printf("ERROR OPENING: %s!\n", wallpaper_file);
    return 1;
  }

  int res = fputs(path, f);
  printf("RESULT: %d\n", res);

  fclose(f);
  return res;
}
