cmake_minimum_required(VERSION 3.11) # FetchContent needs 3.11+
project(CppCalc)

set(CMAKE_CXX_STANDARD 11)

include(FetchContent)
FetchContent_Declare(
  googletest
  GIT_REPOSITORY https://github.com/google/googletest.git
  GIT_TAG        v1.14.0
)
# For Windows: do not override the build status
set(gtest_force_shared_crt ON CACHE BOOL "" FORCE)
FetchContent_MakeAvailable(googletest)

include_directories(logic)

add_library(calc_logic logic/calc.cpp logic/calc.h)

add_executable(test_calc tests/test_calc.cpp)
target_link_libraries(test_calc calc_logic GTest::gtest_main)

enable_testing()
add_test(NAME CalcAddTest COMMAND test_calc)
