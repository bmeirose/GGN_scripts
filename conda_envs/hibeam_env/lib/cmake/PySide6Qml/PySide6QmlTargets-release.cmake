#----------------------------------------------------------------
# Generated CMake target import file for configuration "Release".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "PySide6Qml::pyside6qml" for configuration "Release"
set_property(TARGET PySide6Qml::pyside6qml APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(PySide6Qml::pyside6qml PROPERTIES
  IMPORTED_LINK_DEPENDENT_LIBRARIES_RELEASE "PySide6::pyside6;Shiboken6::libshiboken;Qt6::Core;Qt6::Qml"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libpyside6qml.cpython-39-x86_64-linux-gnu.so.6.9.1"
  IMPORTED_SONAME_RELEASE "libpyside6qml.cpython-39-x86_64-linux-gnu.so.6.9"
  )

list(APPEND _cmake_import_check_targets PySide6Qml::pyside6qml )
list(APPEND _cmake_import_check_files_for_PySide6Qml::pyside6qml "${_IMPORT_PREFIX}/lib/libpyside6qml.cpython-39-x86_64-linux-gnu.so.6.9.1" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
