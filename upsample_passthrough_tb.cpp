#include "verilated.h"

#include "Vupsample_passthrough.h"

#include <iostream>

using namespace std;

int main() {

  Vupsample_passthrough p;
  p.rst = 0;
  p.clk = 0;
  p.en = 0;

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

  p.eval();


  int num_valids = 0;
  for (int i = 0; i < 10; i++) {

    for (int j = 0; j < 2; j++) {
      p.en = j % 2 == 0;

      p.clk = 0;
      p.eval();

      p.clk = 1;
      p.eval();

      if (p.valid == 1) {
        num_valids++;
      }

    }
  }

  cout << "num_valids = " << num_valids << endl;

  assert(num_valids == 20);

  cout << "Test passed" << endl;
}
