#include "verilated.h"

#include "Vtwo_II_upsample.h"

#include <iostream>
#include "tb_utils.h"

using namespace std;

void check_total_output() {

  cout << "Starting total output for upsample with inner loop II = 2 clk" << endl;
  Vtwo_II_upsample p;
  p.rst = 0;
  p.clk = 0;
  p.en = 0;
  reset(p);

  assert(p.valid == 0);
  assert(p.x_valid == 0);

  int num_valids = 0;
  int num_x_valids = 0;

  for (int t = 0; t < 600; t++) {
    bool set_en_cycle = t % 5 == 0;

    if (set_en_cycle) {
      set_sig(p, en, 1);
    } else {
      set_sig(p, en, 0);
    }

    if (set_en_cycle && num_x_valids < 10) {
      assert(p.x_valid == 1);
      assert(p.valid == 1);
    }

    if (p.x_valid) {
      num_x_valids++;
    }

    if (p.valid) {
      cout << t << ":p valid" << endl;
      num_valids++;
    }

    pos(p, clk);
  }

  cout << "num_x_valids = " << num_x_valids << endl;
  cout << "num_valids = " << num_valids << endl;

  assert(num_x_valids == 10);
  assert(num_valids == num_x_valids*2);

  cout << "total output test passed" << endl;
}

int main() {

  Vtwo_II_upsample p;
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

  assert(p.valid == 0);

  // Add the first input
  p.en = 1;
  p.clk = 0;
  p.eval();

  assert(p.valid == 1);

  // commit the input en 
  set_sig(p, clk, 1);
  set_sig(p, clk, 0);

  // stop input en, so that we can read out the next elements from the system, without a hazard
  set_sig(p, en, 0);
  assert(p.valid == 0);

  set_sig(p, clk, 1);
  set_sig(p, clk, 0);

  assert(p.valid == 1);

  pos(p, clk);

  set_sig(p, en, 1);
  assert(p.valid == 1);

  pos(p, clk);

  set_sig(p, en, 1);
  assert(p.valid == 1);

  pos(p, clk);

  set_sig(p, en, 0);
  assert(p.valid == 0);

  pos(p, clk);
  assert(p.valid == 1);

  cout << "Test passed" << endl;

  check_total_output();
}

