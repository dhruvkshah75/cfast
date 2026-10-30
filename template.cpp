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

    int t;
    cin >> t;  
    while (t--) solve();
}
