#include "algorithm.h"

using namespace dbhc;
using namespace std;

template<typename A, typename B>
set<A> range(const std::map<A, B>& m) {
  set<A> d;
  for (auto p : m) {
    d.insert(p.second);
  }
  return d;
}

template<typename A, typename B>
set<A> domain(const std::map<A, B>& m) {
  set<A> d;
  for (auto p : m) {
    d.insert(p.first);
  }
  return d;
}

template<typename T>
class LinearExpr {
  public:

    map<string, T> coefficients;
    T d; 

    T value(const std::string& v) const {
      return map_find(v, coefficients);
    }

    vector<string> lowerVars(const std::string& v) const {
      vector<string> s;
      for (auto m : allVars()) {
        if (value(m) < value(v)) {
          s.push_back(m);
        }
      }

      sort_lt(s, [this](const string& n) { return map_find(n, coefficients); });
      return s;
    }

    set<string> allVars() const {
      return domain(coefficients);
    }
};

template<typename T>
LinearExpr<T> lexp(const std::map<string, T>& values, const T& d) {
  return LinearExpr<T>{values, d};
}

typedef pair<int, int> Interval;

class EventTrigger {
  public:

    LinearExpr<int> sched;
    map<string, Interval> variableBounds;

    set<string> allVars() const {
      return sched.allVars();
    }
    void setBounds(const std::string& name, const int start, const int end) {
      variableBounds[name] = {start, end};
    }

    int maxValue(const std::string& var) const {
      return map_find(var, variableBounds).second;
    }
};

template<typename Event>
class ControlPath {
  public:

    string name;
    map<Event, EventTrigger> eventSchedules;
};

string sepList(const string& ld, const string& rd, const string& sep, const vector<string>& str) {
  string s = ld;
  for (size_t i = 0; i < str.size(); i++) {
    s += str[i];
    if (i < (str.size() - 1)) {
      s += sep; 
    }
  }
  s += rd;
  return s;
}

string commaList(const vector<string>& str) {
  return sepList("(", ")", ", ", str);
}

void printVerilog(const ControlPath<string>& p) {
  vector<string> varStrings{"input clk", "input rst", "input valid"};
  for (auto s : p.eventSchedules) {
    varStrings.push_back(string("output ") + s.first);
    for (auto v : s.second.allVars()) {
      if (!elem(v, varStrings)) {
        string vn = s.first + "_" + v;
        varStrings.push_back(string("output reg [31:0] ") + vn);
      }
    }
  }
  cout << "module " << p.name << commaList(varStrings) << ";\n";

  cout << "\treg [31:0] n_valids;\n";
  cout << endl;

  cout << "\talways @(posedge clk) begin\n";
  cout << "\t\tif (rst) begin\n";
  cout << "\t\t\tn_valids <= 0;" << endl;
  // Set all counters to zero
  for (auto s : p.eventSchedules) {
    for (auto v : s.second.allVars()) {
      string vn = s.first + "_" + v;
      cout << "\t\t\t" << vn + " <= 0;\n";
    }
  }

  cout << "\t\tend else if (valid) begin\n";
  // Increment counters
  cout << "\t\t\tn_valids <= n_valids + 1;" << endl;
  // Increment variables if needed 
  for (auto s : p.eventSchedules) {
    for (auto v : s.second.allVars()) {
      string vn = s.first + "_" + v;
      varStrings.push_back(string("output [31:0] ") + vn);
      vector<string> lower = s.second.sched.lowerVars(v);
      vector<string> lv{s.first};

      for (auto lowerVar : lower) {
        string lowerVarN = s.first + "_" + lowerVar;
        lv.push_back("(" + lowerVarN + " == " + to_string(s.second.maxValue(lowerVar)) + ")");
      }
      cout << "\t\t\tif " + sepList("(", ")", " && ", lv) << " begin" << endl;
      cout << "\t\t\t\t" << vn + " <= (" + vn + " + 1) % " + to_string(s.second.maxValue(v) + 1) + ";\n";
      cout << "\t\t\tend" << endl;
    }
  }

  cout << "\t\tend else begin\n";
  cout << "\t\t\t// valid == 0, do nothing\n";
  cout << "\t\tend\n";
  cout << endl;
  cout << "\tend\n";
  cout << endl;

  // Create assignments to output
  for (auto s : p.eventSchedules) {
    vector<string> sums;
    for (auto v : s.second.allVars()) {
      string vn = s.first + "_" + v;
      sums.push_back("(" + vn + " * " + to_string(s.second.sched.value(v)) + ")");

    }
    sums.push_back(to_string(s.second.sched.d));
    cout << "\tassign " << s.first << " = " << sepList("(", ")", " + ", sums) << " == n_valids;" << endl;
  }

  cout << "endmodule\n";
}

class Action {
  public:

    vector<pair<string, Interval> > surroundingLoops;

    bool isLoad;

    string opName;
    
    int elemWidth;
    int lanes;

    string resName;
    string sourceName;

    LinearExpr<int> addr;
};

class HWProgram {
  public:

    std::vector<Action> actions;
};

int main() {
  ControlPath<string> p;
  p.name = "one_var_path";
  EventTrigger aSched;
  aSched.sched = lexp({{"x", 1}}, 0);
  aSched.setBounds("x", 0, 7);
  p.eventSchedules["do_a"] = aSched;
  printVerilog(p);

  {
    ControlPath<string> p;
    p.name = "two_var_path";
    
    EventTrigger aSched;
    aSched.sched = lexp({{"x", 3}, {"y", 1}}, 0);
    aSched.setBounds("x", 0, 7);
    aSched.setBounds("y", 0, 2);
    p.eventSchedules["do_a"] = aSched;

    printVerilog(p);
  }

  {
    HWProgram p;
    p.addVar("x", 0, 5);
    p.addVar("y", 0, 15);
    // First we need to add a store instruction to record current value?
    p.addLoad("x", "y", "reg_ld", 16, 1, "in_0");
    // Next: Create a program with actions as well as a control path?
    //  Form of the program: control path connected to "actions" with the
    //  actions connected by a datapath?
    //
    //  Program is a vector of instructions?
  }
}
