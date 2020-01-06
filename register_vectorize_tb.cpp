#include "verilated.h"

#include "Vregister_vectorize.h"

#include <iostream>
#include "tb_utils.h"

using namespace std;

void check_total_output() {

  cout << "Starting total output register vectorize" << endl;
  Vregister_vectorize p;
  p.rst = 0;
  p.clk = 0;
  p.en = 0;
  reset(p);

  assert(p.valid == 0);
  assert(p.x_valid == 0);

  int num_valids = 0;
  int num_x_valids = 0;
  int in_pix = 0;

  for (int t = 0; t < 100; t++) {
    bool set_en_cycle = t % 5 == 0;

    cout << "t = " << t << endl;
    if (set_en_cycle) {
      set_sig(p, en, 1);
      set_sig(p, in, in_pix);
      in_pix++;
    } else {
      set_sig(p, en, 0);
    }

    //if (set_en_cycle && num_x_valids < 5) {
      //assert(p.x_valid == 1);
    //}

    if (p.x_valid) {
      num_x_valids++;
    }

    if (p.valid) {
      cout << t << ":p valid" << endl;
      cout << "\tres_pt : " << p.res_pt << endl;
      cout << "\tres_reg: " << p.res_reg << endl;
      num_valids++;
    }

    pos(p, clk);
  }

  // If 10 pixels are sent in I expect to get 5 data valids out
  // with each valid corresponding to a pair of values written
  // in.
  cout << "num_x_valids = " << num_x_valids << endl;
  cout << "num_valids = " << num_valids << endl;

  assert(num_x_valids == 5);
  assert(num_valids == 5);

  cout << "total output test passed" << endl;
}

int main() {
  check_total_output();
  return 0;
}
