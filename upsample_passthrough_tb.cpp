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

  cout << "--- Starting loop" << endl;
  int num_valids = 0;
  int num_x_valids = 0;
  for (int i = 0; i < 20; i++) {

    for (int j = 0; j < 2; j++) {
      p.en = j % 2 == 0;
      p.eval();

      p.clk = 0;
      p.eval();

      //cout << "----------------- Finished evaluating clk = 0 (" << i << ", " << j << ")" << endl;

      if (p.x_valid) {
        num_x_valids++;
        //cout << "\tx valid at " << i << ", " << j << endl;
      } else {
        //cout << "\tx not valid at " << i << ", " << j << endl;
      }

      if (p.valid == 1) {
        num_valids++;
        cout << "\tup valid at " << i << ", " << j << endl;
      } else {
        cout << "\tup NOT valid at " << i << ", " << j << endl;
      }

      p.clk = 1;
      p.eval();
  
      cout << "----------------- Finished evaluating clock edge (" << i << ", " << j << ")" << endl;

    }
  }

  cout << "num_x_valids = " << num_x_valids << endl;
  cout << "num_valids = " << num_valids << endl;

  assert(num_x_valids == 10);
  assert(num_valids == 20);

  cout << "Test passed" << endl;
}
