window.BENCHMARK_DATA = {
  "lastUpdate": 1744770845992,
  "repoUrl": "https://github.com/iausathub/score",
  "entries": {
    "Benchmark": [
      {
        "commit": {
          "author": {
            "email": "michelle.dadighat@noirlab.edu",
            "name": "Michelle Dadighat",
            "username": "mdadighat"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "3ba4c23dc759571892d4a623ade0623c8757ba79",
          "message": "Ignore score/settings to fix failing test",
          "timestamp": "2025-04-15T19:32:47-07:00",
          "tree_id": "0285a1ae5cd275014b2d76b562423642264a40d4",
          "url": "https://github.com/iausathub/score/commit/3ba4c23dc759571892d4a623ade0623c8757ba79"
        },
        "date": 1744770845712,
        "tool": "pytest",
        "benches": [
          {
            "name": "repository/tests/test_benchmark.py::test_benchmark_satellite_query",
            "value": 56.32946144398008,
            "unit": "iter/sec",
            "range": "stddev: 0.010637784552795189",
            "extra": "mean: 17.752699464284863 msec\nrounds: 56"
          },
          {
            "name": "repository/tests/test_benchmark.py::test_benchmark_view_satellite_observations",
            "value": 193.54912002242853,
            "unit": "iter/sec",
            "range": "stddev: 0.00012209831474394912",
            "extra": "mean: 5.166647101697594 msec\nrounds: 59"
          },
          {
            "name": "repository/tests/test_benchmark.py::test_benchmark_api_observations",
            "value": 1.1868940439308067,
            "unit": "iter/sec",
            "range": "stddev: 0.0410754224324007",
            "extra": "mean: 842.5351909999961 msec\nrounds: 5"
          },
          {
            "name": "repository/tests/test_benchmark.py::test_benchmark_api_satellite_observations",
            "value": 1.167008613922346,
            "unit": "iter/sec",
            "range": "stddev: 0.03762168411271601",
            "extra": "mean: 856.891704200001 msec\nrounds: 5"
          }
        ]
      }
    ]
  }
}