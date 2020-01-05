#include "verilated.h"

#include "Vpassthrough.h"

#include <iostream>

using namespace std;

void test_valid_three() {

  Vpassthrough p;
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
  for (int i = 0; i < 100; i++) {
    p.en = 1;
    p.eval();

    p.clk = 0;
    p.eval();


    if (p.valid == 1) {
      num_valids++;
      //cout << "\tup valid at " << i << ", " << j << endl;
    } else {
      //cout << "\tup NOT valid at " << i << ", " << j << endl;
    }

    p.clk = 1;
    p.eval();
  }


  cout << "num_x_valids = " << num_x_valids << endl;
  cout << "num_valids = " << num_valids << endl;

  assert(num_valids == 10);

  cout << "Valid three test passed" << endl;
}

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

  p.rst = 0;

  p.en = 1;
  p.eval();

  assert(p.valid == 1);

  int num_valids = 0;
  for (int i = 0; i < 30; i++) {

    if (p.valid == 1) {
      num_valids++;
    }

    if (i % 3) {
      p.en = p.en == 0 ? 1 : 0;
    }

    p.clk = 0;
    p.eval();
    
    p.clk = 1;
    p.eval();
  }

  cout << "num_valids = " << num_valids << endl;

  assert(num_valids == 10);

  cout << "Basic Test passed" << endl;

  test_valid_three();
}
