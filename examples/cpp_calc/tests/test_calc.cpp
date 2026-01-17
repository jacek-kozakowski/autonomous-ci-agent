#include "../logic/calc.h"
#include <gtest/gtest.h>

TEST(CalcTest, HandlesAddition) {
  Calculator calc;
  EXPECT_EQ(calc.add(2, 3), 5);
}

TEST(CalcTest, HandlesNegativeAddition) {
  Calculator calc;
  EXPECT_EQ(calc.add(-1, -1), -2);
}
