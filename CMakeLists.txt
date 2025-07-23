cmake_minimum_required(VERSION 3.18)
project(wallpv LANGUAGES C)

find_package(PkgConfig REQUIRED)
pkg_check_modules(GTK4 REQUIRED IMPORTED_TARGET gtk4)

set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

add_executable(wallpv main.c fileio.c)
target_link_libraries(wallpv PRIVATE PkgConfig::GTK4)
