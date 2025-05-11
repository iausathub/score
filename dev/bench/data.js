window.BENCHMARK_DATA = {
  "lastUpdate": 1746940666937,
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
      },
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
          "id": "3f1b4daef0014d95b051a8b79599abaca3bf3af3",
          "message": "Update .lighthouserc.json to use production URL",
          "timestamp": "2025-04-21T11:34:20-07:00",
          "tree_id": "6633aa69a9e9adfac3768d23281aec58abb75b4d",
          "url": "https://github.com/iausathub/score/commit/3f1b4daef0014d95b051a8b79599abaca3bf3af3"
        },
        "date": 1745260536562,
        "tool": "pytest",
        "benches": [
          {
            "name": "repository/tests/test_benchmark.py::test_benchmark_satellite_query",
            "value": 56.55813730412275,
            "unit": "iter/sec",
            "range": "stddev: 0.009446649823477468",
            "extra": "mean: 17.68092175000088 msec\nrounds: 56"
          },
          {
            "name": "repository/tests/test_benchmark.py::test_benchmark_view_satellite_observations",
            "value": 200.96388237604654,
            "unit": "iter/sec",
            "range": "stddev: 0.00015923519667272696",
            "extra": "mean: 4.976018517241747 msec\nrounds: 58"
          },
          {
            "name": "repository/tests/test_benchmark.py::test_benchmark_api_observations",
            "value": 2.1106785886033825,
            "unit": "iter/sec",
            "range": "stddev: 0.041291980584570766",
            "extra": "mean: 473.7812783999914 msec\nrounds: 5"
          },
          {
            "name": "repository/tests/test_benchmark.py::test_benchmark_api_satellite_observations",
            "value": 2.3947045316299356,
            "unit": "iter/sec",
            "range": "stddev: 0.01589213936583098",
            "extra": "mean: 417.5880518000099 msec\nrounds: 5"
          }
        ]
      },
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
          "id": "ee25a6f0234916d6e11fc60db2a97396839dcf74",
          "message": "Merge pull request #94 from iausathub/develop\n\nFix email validation/whitespace issue and extend SatChecker request timeout",
          "timestamp": "2025-05-10T18:49:45-07:00",
          "tree_id": "eabc5a187c8bf5693e75cf0537d2b8e06c6ac642",
          "url": "https://github.com/iausathub/score/commit/ee25a6f0234916d6e11fc60db2a97396839dcf74"
        },
        "date": 1746928268628,
        "tool": "pytest",
        "benches": [
          {
            "name": "repository/tests/test_benchmark.py::test_benchmark_satellite_query",
            "value": 56.78457608423396,
            "unit": "iter/sec",
            "range": "stddev: 0.00951796508868403",
            "extra": "mean: 17.610415872729327 msec\nrounds: 55"
          },
          {
            "name": "repository/tests/test_benchmark.py::test_benchmark_view_satellite_observations",
            "value": 173.27907904675465,
            "unit": "iter/sec",
            "range": "stddev: 0.005992003387583782",
            "extra": "mean: 5.7710371355919845 msec\nrounds: 59"
          },
          {
            "name": "repository/tests/test_benchmark.py::test_benchmark_api_observations",
            "value": 1.0715688087866992,
            "unit": "iter/sec",
            "range": "stddev: 0.048446895012090534",
            "extra": "mean: 933.2111869999892 msec\nrounds: 5"
          },
          {
            "name": "repository/tests/test_benchmark.py::test_benchmark_api_satellite_observations",
            "value": 1.0922888066577545,
            "unit": "iter/sec",
            "range": "stddev: 0.05085526705609698",
            "extra": "mean: 915.5087865999974 msec\nrounds: 5"
          }
        ]
      },
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
          "id": "ee25a6f0234916d6e11fc60db2a97396839dcf74",
          "message": "Merge pull request #94 from iausathub/develop\n\nFix email validation/whitespace issue and extend SatChecker request timeout",
          "timestamp": "2025-05-10T18:49:45-07:00",
          "tree_id": "eabc5a187c8bf5693e75cf0537d2b8e06c6ac642",
          "url": "https://github.com/iausathub/score/commit/ee25a6f0234916d6e11fc60db2a97396839dcf74"
        },
        "date": 1746940666011,
        "tool": "pytest",
        "benches": [
          {
            "name": "repository/tests/test_benchmark.py::test_benchmark_satellite_query",
            "value": 57.289551476117374,
            "unit": "iter/sec",
            "range": "stddev: 0.009956554518663034",
            "extra": "mean: 17.455189894738062 msec\nrounds: 57"
          },
          {
            "name": "repository/tests/test_benchmark.py::test_benchmark_view_satellite_observations",
            "value": 192.78109304994743,
            "unit": "iter/sec",
            "range": "stddev: 0.00016108648134009727",
            "extra": "mean: 5.187230677963379 msec\nrounds: 59"
          },
          {
            "name": "repository/tests/test_benchmark.py::test_benchmark_api_observations",
            "value": 2.2251554785446994,
            "unit": "iter/sec",
            "range": "stddev: 0.08677516897133765",
            "extra": "mean: 449.4067985999891 msec\nrounds: 5"
          },
          {
            "name": "repository/tests/test_benchmark.py::test_benchmark_api_satellite_observations",
            "value": 2.37108008191996,
            "unit": "iter/sec",
            "range": "stddev: 0.04731569203347423",
            "extra": "mean: 421.748724400004 msec\nrounds: 5"
          }
        ]
      }
    ]
  }
}