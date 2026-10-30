#include <bits/stdc++.h>
using namespace std;
using i64 = int64_t;
constexpr i64 INF = numeric_limits<i64>::max() / 4;

#ifdef LOCAL
template <class... T> void debug_values(const T&... values) {
    ((cerr << values << ' '), ...);
    cerr << '\n';
}
#define dbg(...) (cerr << "[" << __FILE__ << ":" << __LINE__ << "] (" << #__VA_ARGS__ << "): ", debug_values(__VA_ARGS__))
#else
#define dbg(...) ((void)0)
#endif

void run_case() {
    // Write your solution here.
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int t = 1;
    // cin >> t;  // Uncomment only if the problem input starts with a case count.
    while (t--) run_case();
}
