cmake_minimum_required(VERSION 3.13)

if(TARGET mcufont_generator)
    return()
endif()

if(NOT MCUFONT_CROSSCOMPILING)
    project(mcufont)

    find_package(Freetype REQUIRED)
    find_package(Threads REQUIRED)

    add_executable(mcufont_generator
       encoder/bdf_import.cc
       encoder/datafile.cc
       encoder/encode_rlefont.cc
       encoder/export_bwfont.cc
       encoder/export_rlefont.cc
       encoder/exporttools.cc
       encoder/freetype_import.cc
       encoder/gb2312_in_ucs2.h
       encoder/importtools.cc
       encoder/main.cc
       encoder/optimize_rlefont.cc
    )
    target_include_directories(mcufont_generator PRIVATE encoder)
    target_link_libraries(mcufont_generator Freetype::Freetype Threads::Threads)
else()
    execute_process(
        COMMAND cmake -E make_directory build
        COMMAND cmake -E env CC=gcc CXX=g++ cmake -G "Unix Makefiles" -S ${CMAKE_CURRENT_LIST_DIR} -B build
        WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
    )

    add_custom_target(mcufont_generator
        COMMAND cmake --build ${CMAKE_CURRENT_BINARY_DIR}/build
        WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/build
        BYPRODUCTS ${CMAKE_CURRENT_BINARY_DIR}/build/mcufont_generator
    )
endif()

find_program(clang-format clang-format)

function(mcufont_add_library target)
    cmake_parse_arguments(
        PARSE_ARGV
        1
        PARSED_ARGS
        ""
        ""
        "FONTS"
    )

    if(PARSED_ARGS_UNPARSED_ARGUMENTS)
        message(FATAL_ERROR "unknown argument ${PARSED_ARGS_UNPARSED_ARGUMENTS}")
    endif()

    if(NOT PARSED_ARGS_FONTS)
        message(FATAL_ERROR "need FONTS")
    endif()

    add_library(${target}_mcufont
        mcufont/decoder/mf_bwfont.c
        mcufont/decoder/mf_encoding.c
        mcufont/decoder/mf_font.c
        mcufont/decoder/mf_justify.c
        mcufont/decoder/mf_kerning.c
        mcufont/decoder/mf_rlefont.c
        mcufont/decoder/mf_scaledfont.c
        mcufont/decoder/mf_wordwrap.c
    )

    target_include_directories(${target}_mcufont PUBLIC mcufont/decoder)
    target_include_directories(${target}_mcufont PUBLIC ${CMAKE_CURRENT_BINARY_DIR}/generated/mcufont/${target})

    get_target_property(target_options ${target} COMPILE_OPTIONS)

    target_compile_options(${target}_mcufont PRIVATE ${target_options})
    target_link_libraries(${target}_mcufont PUBLIC ${PARSED_ARGS_FONTS})


    set(CMAKE_CONFIGURABLE_FILE_CONTENT "")

    foreach(font IN LISTS PARSED_ARGS_FONTS)
        set(CMAKE_CONFIGURABLE_FILE_CONTENT
            "${CMAKE_CONFIGURABLE_FILE_CONTENT}\n#include \"${font}.h\"")
    endforeach()

    configure_file("${CMAKE_ROOT}/Modules/CMakeConfigurableFile.in"
        ${CMAKE_CURRENT_BINARY_DIR}/generated/mcufont/${target}/fonts.h
        @ONLY
    )
    unset(CMAKE_CONFIGURABLE_FILE_CONTENT)

    set(CMAKE_CONFIGURABLE_FILE_CONTENT "#pragma once\nnamespace mcufont{\nenum class Font{")

    foreach(font IN LISTS PARSED_ARGS_FONTS)
        set(CMAKE_CONFIGURABLE_FILE_CONTENT
            "${CMAKE_CONFIGURABLE_FILE_CONTENT}\n    ${font},")
    endforeach()

    set(CMAKE_CONFIGURABLE_FILE_CONTENT
        "${CMAKE_CONFIGURABLE_FILE_CONTENT}\n};\nconstexpr char const* font_name(Font font){")

    foreach(font IN LISTS PARSED_ARGS_FONTS)
        set(CMAKE_CONFIGURABLE_FILE_CONTENT
            "${CMAKE_CONFIGURABLE_FILE_CONTENT}\n    if(font == Font::${font}){return \"${font}\";}")
    endforeach()

    set(CMAKE_CONFIGURABLE_FILE_CONTENT
        "${CMAKE_CONFIGURABLE_FILE_CONTENT}\n    return \"\";\n}\n}")


    configure_file("${CMAKE_ROOT}/Modules/CMakeConfigurableFile.in"
        ${CMAKE_CURRENT_BINARY_DIR}/generated/mcufont/${target}/fonts.hpp
        @ONLY
    )
    unset(CMAKE_CONFIGURABLE_FILE_CONTENT)


    target_link_libraries(${target} ${target}_mcufont)
endfunction()

function(mcufont_generate targetname)

    cmake_parse_arguments(
        PARSE_ARGV
        1
        PARSED_ARGS
        "BWFONT"
        "SIZE;ITERATIONS;FONT"
        "RANGES"
    )

    if(PARSED_ARGS_UNPARSED_ARGUMENTS)
        message(FATAL_ERROR "unknown argument ${PARSED_ARGS_UNPARSED_ARGUMENTS}")
    endif()

    if(NOT PARSED_ARGS_SIZE)
        message(FATAL_ERROR "need SIZE")
    endif()

    if(NOT PARSED_ARGS_FONT)
        message(FATAL_ERROR "need FONT")
    endif()

    if(NOT PARSED_ARGS_BWFONT)
        set(PARSED_ARGS_BWFONT 0)
    else()
        set(PARSED_ARGS_BWFONT 1)
    endif()
    
    if(NOT PARSED_ARGS_ITERATIONS)
        set(PARSED_ARGS_ITERATIONS 5)
    endif()

    if(NOT PARSED_ARGS_RANGES)
        message(FATAL_ERROR "need RANGES")
    endif()

    set(filename ${PARSED_ARGS_FONT})
    set(size ${PARSED_ARGS_SIZE})

    set(iname ${CMAKE_CURRENT_SOURCE_DIR}/${filename})

    if(NOT EXISTS ${iname})
        find_file(font_file NAMES ${filename} PATHS /usr/share/fonts)
        file(GLOB_RECURSE font_files /usr/*.ttf)
        foreach(current_file IN LISTS font_files)
            get_filename_component(current_file_no_dir ${current_file} NAME)
            if(${current_file_no_dir} STREQUAL ${filename})
                set(iname ${current_file})
            endif()
        endforeach()
        if(NOT EXISTS ${iname})
            message(FATAL_ERROR "Font file ${filename} not found")
        endif()
    endif()

    set(incname ${CMAKE_CURRENT_BINARY_DIR}/generated/mcufont)
    set(dname ${incname}/fonts)
    set(oname ${dname}/${targetname}.h)

    get_target_property(build_dir mcufont_generator BINARY_DIR)

if(NOT MCUFONT_CROSSCOMPILING)
    set(mcufont_generator_bin ${build_dir}/mcufont_generator)
else()
    set(mcufont_generator_bin ${build_dir}/build/mcufont_generator)
endif()

    set(generate_script ${CMAKE_CURRENT_LIST_DIR}/mcufont/tools/generate.py)
    set(command python 
                ${generate_script}
                ${mcufont_generator_bin}
                ${iname}
                ${oname}
                ${size}
                ${PARSED_ARGS_ITERATIONS}
                ${PARSED_ARGS_BWFONT}
                ${PARSED_ARGS_RANGES}
                )
 
    if(NOT EXISTS ${clang-format})
        add_custom_command(
            COMMAND cmake -E make_directory ${dname}
            COMMAND ${command}
            DEPENDS mcufont_generator ${generate_script} ${iname} ${mcufont_generator_bin}
            OUTPUT ${oname}
        )
    else()
        add_custom_command(
            COMMAND cmake -E make_directory ${dname}
            COMMAND ${command}
            COMMAND ${clang-format} -i ${oname}
            DEPENDS mcufont_generator ${generate_script} ${iname} ${mcufont_generator_bin}
            OUTPUT ${oname}
        )
    endif()

    if(${CMAKE_VERSION} VERSION_LESS "3.19.0")
        set_source_files_properties(
            ${oname}
            PROPERTIES GENERATED TRUE
        )
        add_custom_target(
            ${targetname}_helper
            DEPENDS ${oname}
        )
        add_library(${targetname} INTERFACE)
        add_dependencies(${targetname} ${targetname}_helper)
    else()
        add_library(${targetname} INTERFACE ${oname})
    endif()

    target_include_directories(${targetname} INTERFACE ${dname})

endfunction()
