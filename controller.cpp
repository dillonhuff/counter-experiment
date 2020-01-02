#include "algorithm.h"

using namespace dbhc;
using namespace std;

class Action {
  public:

};

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
};

template<typename Event>
class ControlPath {
  public:

    string name;
    map<Event, EventTrigger> eventSchedules;
};

string commaList(const vector<string>& str) {
  string s = "(";
  for (size_t i = 0; i < str.size(); i++) {
    s += str[i];
    if (i < (str.size() - 1)) {
      s += ", ";
    }
  }
  s += ")";
  return s;
}

void printVerilog(const ControlPath<string>& p) {
  vector<string> varStrings{"input clk", "input rst", "input valid"};
  for (auto s : p.eventSchedules) {
    varStrings.push_back(string("output ") + s.first);
    for (auto v : s.second.allVars()) {
      if (!elem(v, varStrings)) {
        string vn = s.first + "_" + v;
        varStrings.push_back(string("output [31:0] ") + vn);
      }
    }
  }
  cout << "module " << p.name << commaList(varStrings) << ";\n";
  cout << "endmodule\n";
}

int main() {
  ControlPath<string> p;
  p.name = "one_var_path";
  EventTrigger aSched;
  aSched.sched = lexp({{"x", 1}}, 0);
  aSched.setBounds("x", 0, 7);
  p.eventSchedules["do_a"] = aSched;

  printVerilog(p);
}
