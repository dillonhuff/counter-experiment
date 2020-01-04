#include "verilated.h"

#include "Vpassthrough.h"

#include <iostream>

using namespace std;

int main() {

  Vpassthrough p;
  p.rst = 0;
  p.clk = 0;

  p.eval();

  p.rst = 1;
  
  p.clk = 0;
  p.eval();

  p.clk = 1;
  p.eval();

  // Should be reset
  //
  p.clk = 0;
  p.eval();

  assert(p.valid == 0);

  p.en = 1;
  p.eval();

  assert(p.valid == 1);
  
  cout << "Test passed" << endl;
}
