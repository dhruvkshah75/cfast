
#include <bits/stdc++.h>
using namespace std;

typedef long long ll;
typedef unsigned long long ull;
typedef pair<int,int> pii;
typedef pair<ll,ll> pll;
typedef tuple<int,int,int> tiii;

#define all(x) x.begin(), x.end()
#define rall(x) x.rbegin(), x.rend()
#define yes cout << "YES" << endl;
#define no cout << "NO" << endl;
#define setbits(x) __builtin_popcount(x)
#define setbitsll(x) __builtin_popcountll(x)

#ifdef LOCAL
template <typename T1, typename T2>
ostream& operator<<(ostream& os, const pair<T1, T2>& p) {
    return os << "{" << p.first << ", " << p.second << "}";
}

template <typename T>
ostream& operator<<(ostream& os, const vector<T>& v) {
    os << "[";
    for(size_t i = 0; i < v.size(); ++i) {
        os << v[i] << (i + 1 < v.size() ? ", " : "");
    }
    return os << "]";
}

template <class... T> void debug_values(const T&... values) {
    ((cerr << values << ' '), ...);
    cerr << '\n';
}
#define dbg(...) (cerr << "[" << __FILE__ << ":" << __LINE__ << "] (" << #__VA_ARGS__ << "): ", debug_values(__VA_ARGS__))
#else
#define dbg(...) ((void)0)
#endif

void solve() {
    // Write your solution here.
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int t = 0;
    if (!(cin >> t) || t < 0) return 0;
    while (t--) solve();
}
