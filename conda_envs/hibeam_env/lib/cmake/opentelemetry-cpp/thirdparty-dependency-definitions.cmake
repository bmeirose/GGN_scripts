# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0

# Configured from opentelmetry-cpp/cmake/thirdparty-dependency-definitions.cmake.in

#-----------------------------------------------------------------------
# Third party dependencies supported by opentelemetry-cpp
#    Dependencies will be found in this order when find_package(opentelemetry-cpp ...)  is called.
#-----------------------------------------------------------------------
set(OTEL_THIRDPARTY_DEPENDENCIES_SUPPORTED Threads;ZLIB;CURL;nlohmann_json;Protobuf;gRPC;prometheus-cpp;OpenTracing)

#-----------------------------------------------------------------------
# Third party dependency versions used to build opentelemetry-cpp
#-----------------------------------------------------------------------
set(OTEL_Threads_VERSION "")
set(OTEL_ZLIB_VERSION "1.3.1")
set(OTEL_CURL_VERSION "8.14.0")
set(OTEL_nlohmann_json_VERSION "3.12.0")
set(OTEL_Protobuf_VERSION "29.3.0")
set(OTEL_gRPC_VERSION "1.71.0")
set(OTEL_prometheus-cpp_VERSION "1.3.0")
set(OTEL_OpenTracing_VERSION "")


#-----------------------------------------------------------------------
# Set the find_dependecy search mode - empty is default. Options MODULE or CONFIG
#-----------------------------------------------------------------------
set(OTEL_Threads_SEARCH_MODE "")
set(OTEL_ZLIB_SEARCH_MODE "")
set(OTEL_CURL_SEARCH_MODE "")
set(OTEL_nlohmann_json_SEARCH_MODE "CONFIG")
set(OTEL_Protobuf_SEARCH_MODE "CONFIG")
set(OTEL_gRPC_SEARCH_MODE "CONFIG")
set(OTEL_prometheus-cpp_SEARCH_MODE "CONFIG")
set(OTEL_OpenTracing_SEARCH_MODE "CONFIG")

