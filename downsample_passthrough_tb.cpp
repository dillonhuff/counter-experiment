
#include "verilated.h"

#include "Vdownsample_passthrough.h"

#include <iostream>

using namespace std;

int main() {

  Vdownsample_passthrough p;
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

  p.rst = 0;

  p.en = 1;
  p.eval();

  assert(p.valid == 1);

  int num_valids = 0;
  for (int i = 0; i < 10; i++) {

    if (p.valid == 1) {
      num_valids++;
    }

    p.clk = 0;
    p.eval();
    
    p.clk = 1;
    p.eval();
  }

  cout << "num_valids = " << num_valids << endl;

  assert(num_valids == 5);

  cout << "Test passed" << endl;
}
