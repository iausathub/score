window.BENCHMARK_DATA = {
  "lastUpdate": 1766886910180,
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
          "id": "04f48100d812b9f8050e4dc9d1ad1c07eacda479",
          "message": "Merge pull request #95 from iausathub/develop\n\nAdd NSF logo to About page",
          "timestamp": "2025-05-26T10:22:39-07:00",
          "tree_id": "1fcb64601890a6eeccd5bd5b201e533c3f8e2a7e",
          "url": "https://github.com/iausathub/score/commit/04f48100d812b9f8050e4dc9d1ad1c07eacda479"
        },
        "date": 1748280242119,
        "tool": "pytest",
        "benches": [
          {
            "name": "repository/tests/test_benchmark.py::test_benchmark_satellite_query",
            "value": 59.58877133425775,
            "unit": "iter/sec",
            "range": "stddev: 0.009177794977219033",
            "extra": "mean: 16.78168516666658 msec\nrounds: 54"
          },
          {
            "name": "repository/tests/test_benchmark.py::test_benchmark_view_satellite_observations",
            "value": 174.71009676643618,
            "unit": "iter/sec",
            "range": "stddev: 0.005724543925171093",
            "extra": "mean: 5.723767649999445 msec\nrounds: 60"
          },
          {
            "name": "repository/tests/test_benchmark.py::test_benchmark_api_observations",
            "value": 1.4511852562980183,
            "unit": "iter/sec",
            "range": "stddev: 0.07459116034260246",
            "extra": "mean: 689.0918962000796 msec\nrounds: 5"
          },
          {
            "name": "repository/tests/test_benchmark.py::test_benchmark_api_satellite_observations",
            "value": 1.4669836842271822,
            "unit": "iter/sec",
            "range": "stddev: 0.029819880895161938",
            "extra": "mean: 681.6708397999719 msec\nrounds: 5"
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
          "id": "5837ddea09bfbf8eacb89e4d30824f293a2c447a",
          "message": "Merge pull request #98 from iausathub/develop\n\nUpdate workflow permissions",
          "timestamp": "2025-06-16T12:45:13-07:00",
          "tree_id": "72fd847a8d2811230a572eec26ba5071b265cf0f",
          "url": "https://github.com/iausathub/score/commit/5837ddea09bfbf8eacb89e4d30824f293a2c447a"
        },
        "date": 1750103198172,
        "tool": "pytest",
        "benches": [
          {
            "name": "repository/tests/test_benchmark.py::test_benchmark_satellite_query",
            "value": 55.18022125230226,
            "unit": "iter/sec",
            "range": "stddev: 0.011447759494589862",
            "extra": "mean: 18.122435490565877 msec\nrounds: 53"
          },
          {
            "name": "repository/tests/test_benchmark.py::test_benchmark_view_satellite_observations",
            "value": 188.63808029275648,
            "unit": "iter/sec",
            "range": "stddev: 0.00016173139341275547",
            "extra": "mean: 5.301156576912001 msec\nrounds: 52"
          },
          {
            "name": "repository/tests/test_benchmark.py::test_benchmark_api_observations",
            "value": 1.1069462970051762,
            "unit": "iter/sec",
            "range": "stddev: 0.030216053381057113",
            "extra": "mean: 903.3861919999936 msec\nrounds: 5"
          },
          {
            "name": "repository/tests/test_benchmark.py::test_benchmark_api_satellite_observations",
            "value": 1.1325676146376167,
            "unit": "iter/sec",
            "range": "stddev: 0.027250798423275147",
            "extra": "mean: 882.949492000057 msec\nrounds: 5"
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
          "id": "805667420d60105097dc175894f52c9f9b22ca4d",
          "message": "Merge pull request #100 from iausathub/develop\n\nAdd potentially discrepant flag",
          "timestamp": "2025-07-03T10:10:02-07:00",
          "tree_id": "e2770e58d7e4a3cf263a666aa4c1859c7d6e9bfd",
          "url": "https://github.com/iausathub/score/commit/805667420d60105097dc175894f52c9f9b22ca4d"
        },
        "date": 1751562683544,
        "tool": "pytest",
        "benches": [
          {
            "name": "repository/tests/test_benchmark.py::test_benchmark_satellite_query",
            "value": 59.16708314218009,
            "unit": "iter/sec",
            "range": "stddev: 0.0075912039221354335",
            "extra": "mean: 16.90128948214285 msec\nrounds: 56"
          },
          {
            "name": "repository/tests/test_benchmark.py::test_benchmark_view_satellite_observations",
            "value": 193.77986803446458,
            "unit": "iter/sec",
            "range": "stddev: 0.00016901210659485655",
            "extra": "mean: 5.160494793102788 msec\nrounds: 58"
          },
          {
            "name": "repository/tests/test_benchmark.py::test_benchmark_api_observations",
            "value": 1.599939376377095,
            "unit": "iter/sec",
            "range": "stddev: 0.03290497985250068",
            "extra": "mean: 625.0236820000026 msec\nrounds: 5"
          },
          {
            "name": "repository/tests/test_benchmark.py::test_benchmark_api_satellite_observations",
            "value": 1.639476853507384,
            "unit": "iter/sec",
            "range": "stddev: 0.02209890045148647",
            "extra": "mean: 609.9506668000032 msec\nrounds: 5"
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
          "id": "c7d3811ec0ad7b8a4bd6c193f0a06d4aa4ee7883",
          "message": "Merge pull request #101 from iausathub/develop\n\nFix ORCID validation to allow 'X' at the end",
          "timestamp": "2025-08-21T11:24:19-07:00",
          "tree_id": "069b354cf7c15ec63f2db2b0f8a652c8186dc9c4",
          "url": "https://github.com/iausathub/score/commit/c7d3811ec0ad7b8a4bd6c193f0a06d4aa4ee7883"
        },
        "date": 1755800737122,
        "tool": "pytest",
        "benches": [
          {
            "name": "repository/tests/test_benchmark.py::test_benchmark_satellite_query",
            "value": 55.92323998449127,
            "unit": "iter/sec",
            "range": "stddev: 0.009450871169143308",
            "extra": "mean: 17.881653499999675 msec\nrounds: 56"
          },
          {
            "name": "repository/tests/test_benchmark.py::test_benchmark_view_satellite_observations",
            "value": 198.78214410589268,
            "unit": "iter/sec",
            "range": "stddev: 0.00006115047486208052",
            "extra": "mean: 5.030632929823379 msec\nrounds: 57"
          },
          {
            "name": "repository/tests/test_benchmark.py::test_benchmark_api_observations",
            "value": 1.0392948267700448,
            "unit": "iter/sec",
            "range": "stddev: 0.07412221515210661",
            "extra": "mean: 962.1908762000032 msec\nrounds: 5"
          },
          {
            "name": "repository/tests/test_benchmark.py::test_benchmark_api_satellite_observations",
            "value": 1.0651621373614997,
            "unit": "iter/sec",
            "range": "stddev: 0.07695430654156521",
            "extra": "mean: 938.8242080000026 msec\nrounds: 5"
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
          "id": "dbd2c51d8777c8140f5b53a972c4a1dcb093b2d6",
          "message": "Merge pull request #104 from iausathub/develop\n\nAdd solar position and satellite altitude to reference data",
          "timestamp": "2025-08-29T11:28:38-07:00",
          "tree_id": "84a1cdbfe3353a70957b3dfa8bff66eb5063f860",
          "url": "https://github.com/iausathub/score/commit/dbd2c51d8777c8140f5b53a972c4a1dcb093b2d6"
        },
        "date": 1756492204399,
        "tool": "pytest",
        "benches": [
          {
            "name": "repository/tests/test_benchmark.py::test_benchmark_satellite_query",
            "value": 55.123344724902836,
            "unit": "iter/sec",
            "range": "stddev: 0.010468995495091178",
            "extra": "mean: 18.141134305085707 msec\nrounds: 59"
          },
          {
            "name": "repository/tests/test_benchmark.py::test_benchmark_view_satellite_observations",
            "value": 194.92662930347134,
            "unit": "iter/sec",
            "range": "stddev: 0.00013920357394079982",
            "extra": "mean: 5.13013539285672 msec\nrounds: 56"
          },
          {
            "name": "repository/tests/test_benchmark.py::test_benchmark_api_observations",
            "value": 1.3110425371186167,
            "unit": "iter/sec",
            "range": "stddev: 0.054092918209789106",
            "extra": "mean: 762.751757999996 msec\nrounds: 5"
          },
          {
            "name": "repository/tests/test_benchmark.py::test_benchmark_api_satellite_observations",
            "value": 1.3046655440261352,
            "unit": "iter/sec",
            "range": "stddev: 0.03431786604414582",
            "extra": "mean: 766.4799646000063 msec\nrounds: 5"
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
          "id": "2f70eff8f5b461c0aef17a81de45c00f599577d5",
          "message": "Merge pull request #105 from iausathub/develop\n\nFix bug when observer altitude is zero; update IAU CPS to shorter name",
          "timestamp": "2025-09-22T21:46:07-07:00",
          "tree_id": "1123a149564f15fa203680c17b9676da178108d4",
          "url": "https://github.com/iausathub/score/commit/2f70eff8f5b461c0aef17a81de45c00f599577d5"
        },
        "date": 1758602849394,
        "tool": "pytest",
        "benches": [
          {
            "name": "repository/tests/test_benchmark.py::test_benchmark_satellite_query",
            "value": 54.65432125098914,
            "unit": "iter/sec",
            "range": "stddev: 0.009492393682944956",
            "extra": "mean: 18.296814910713064 msec\nrounds: 56"
          },
          {
            "name": "repository/tests/test_benchmark.py::test_benchmark_view_satellite_observations",
            "value": 196.34662174095294,
            "unit": "iter/sec",
            "range": "stddev: 0.00013164527664385017",
            "extra": "mean: 5.09303389655125 msec\nrounds: 58"
          },
          {
            "name": "repository/tests/test_benchmark.py::test_benchmark_api_observations",
            "value": 1.0878643315167027,
            "unit": "iter/sec",
            "range": "stddev: 0.05088220396626306",
            "extra": "mean: 919.2322710000042 msec\nrounds: 5"
          },
          {
            "name": "repository/tests/test_benchmark.py::test_benchmark_api_satellite_observations",
            "value": 1.0973784204999464,
            "unit": "iter/sec",
            "range": "stddev: 0.025396376125370844",
            "extra": "mean: 911.2626796000029 msec\nrounds: 5"
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
          "id": "017a74652c703e34a6f0584de2e23d8291f01bf2",
          "message": "Merge pull request #109 from iausathub/develop\n\nAdd data visualization page and filterable all-sky plot and graphs",
          "timestamp": "2025-10-28T09:48:13-07:00",
          "tree_id": "e842d42cb66473fae627adb2417330b60aa634e8",
          "url": "https://github.com/iausathub/score/commit/017a74652c703e34a6f0584de2e23d8291f01bf2"
        },
        "date": 1761670179689,
        "tool": "pytest",
        "benches": [
          {
            "name": "repository/tests/test_benchmark.py::test_benchmark_satellite_query",
            "value": 56.76889978622002,
            "unit": "iter/sec",
            "range": "stddev: 0.008025303787123792",
            "extra": "mean: 17.615278854545252 msec\nrounds: 55"
          },
          {
            "name": "repository/tests/test_benchmark.py::test_benchmark_view_satellite_observations",
            "value": 186.20654879488595,
            "unit": "iter/sec",
            "range": "stddev: 0.00008083372450296064",
            "extra": "mean: 5.370380400001615 msec\nrounds: 55"
          },
          {
            "name": "repository/tests/test_benchmark.py::test_benchmark_api_observations",
            "value": 1.2240961374925048,
            "unit": "iter/sec",
            "range": "stddev: 0.036485198509882716",
            "extra": "mean: 816.9292994000017 msec\nrounds: 5"
          },
          {
            "name": "repository/tests/test_benchmark.py::test_benchmark_api_satellite_observations",
            "value": 1.334660528660765,
            "unit": "iter/sec",
            "range": "stddev: 0.07362720320488689",
            "extra": "mean: 749.2541950000032 msec\nrounds: 5"
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
          "id": "aec585de67c96d7e52bbb02b3310cb877170f649",
          "message": "Fix for search results and downloaded results being out of sync (#111)\n\n* Update obs_id field used with download results button after each search\n\n* Update tests",
          "timestamp": "2025-11-04T10:13:23-08:00",
          "tree_id": "9bb915f1a4bba2edcf2974b6994b0abf2c545c10",
          "url": "https://github.com/iausathub/score/commit/aec585de67c96d7e52bbb02b3310cb877170f649"
        },
        "date": 1762280092745,
        "tool": "pytest",
        "benches": [
          {
            "name": "repository/tests/test_benchmark.py::test_benchmark_satellite_query",
            "value": 56.50780627089959,
            "unit": "iter/sec",
            "range": "stddev: 0.008706381800064392",
            "extra": "mean: 17.69666999999928 msec\nrounds: 53"
          },
          {
            "name": "repository/tests/test_benchmark.py::test_benchmark_view_satellite_observations",
            "value": 172.22818726731555,
            "unit": "iter/sec",
            "range": "stddev: 0.005730813933430236",
            "extra": "mean: 5.806250509087104 msec\nrounds: 55"
          },
          {
            "name": "repository/tests/test_benchmark.py::test_benchmark_api_observations",
            "value": 0.9824665938505941,
            "unit": "iter/sec",
            "range": "stddev: 0.09646835531498349",
            "extra": "mean: 1.0178463127999975 sec\nrounds: 5"
          },
          {
            "name": "repository/tests/test_benchmark.py::test_benchmark_api_satellite_observations",
            "value": 1.0159614466022424,
            "unit": "iter/sec",
            "range": "stddev: 0.08455317862583188",
            "extra": "mean: 984.2893186000083 msec\nrounds: 5"
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
          "id": "62d95ee18adb83310ab7bd5b3db719d985add315",
          "message": "Add PlanetLabs satellites to constellation visualizations (#114)\n\n* Add PlanetLabs satellites as a constellation set for visualizations",
          "timestamp": "2025-12-03T13:40:08-08:00",
          "tree_id": "ac1447b90766fb1da668ebdf4df67bd02301ae15",
          "url": "https://github.com/iausathub/score/commit/62d95ee18adb83310ab7bd5b3db719d985add315"
        },
        "date": 1764798082904,
        "tool": "pytest",
        "benches": [
          {
            "name": "repository/tests/test_benchmark.py::test_benchmark_satellite_query",
            "value": 53.56770614727396,
            "unit": "iter/sec",
            "range": "stddev: 0.010994985765774627",
            "extra": "mean: 18.667963814815874 msec\nrounds: 54"
          },
          {
            "name": "repository/tests/test_benchmark.py::test_benchmark_view_satellite_observations",
            "value": 168.26702084531792,
            "unit": "iter/sec",
            "range": "stddev: 0.006031470134573298",
            "extra": "mean: 5.942935192982739 msec\nrounds: 57"
          },
          {
            "name": "repository/tests/test_benchmark.py::test_benchmark_api_observations",
            "value": 2.4364573934058935,
            "unit": "iter/sec",
            "range": "stddev: 0.03210647375389313",
            "extra": "mean: 410.43196680000733 msec\nrounds: 5"
          },
          {
            "name": "repository/tests/test_benchmark.py::test_benchmark_api_satellite_observations",
            "value": 7.61724497988685,
            "unit": "iter/sec",
            "range": "stddev: 0.014218679220657397",
            "extra": "mean: 131.28106062499967 msec\nrounds: 8"
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
            "email": "michelle.dadighat@noirlab.edu",
            "name": "Michelle Dadighat",
            "username": "mdadighat"
          },
          "distinct": true,
          "id": "7aa17275348628015cf00c02e61eff12f4039485",
          "message": "Add space to Planet Labs name",
          "timestamp": "2025-12-03T14:06:27-08:00",
          "tree_id": "9b3bb9f7b29456c21bf42419e63dc38507c3dd2f",
          "url": "https://github.com/iausathub/score/commit/7aa17275348628015cf00c02e61eff12f4039485"
        },
        "date": 1764799674530,
        "tool": "pytest",
        "benches": [
          {
            "name": "repository/tests/test_benchmark.py::test_benchmark_satellite_query",
            "value": 55.397141161186184,
            "unit": "iter/sec",
            "range": "stddev: 0.009432870597958935",
            "extra": "mean: 18.051473037035468 msec\nrounds: 54"
          },
          {
            "name": "repository/tests/test_benchmark.py::test_benchmark_view_satellite_observations",
            "value": 167.0254882067451,
            "unit": "iter/sec",
            "range": "stddev: 0.00669232451208484",
            "extra": "mean: 5.987110175437381 msec\nrounds: 57"
          },
          {
            "name": "repository/tests/test_benchmark.py::test_benchmark_api_observations",
            "value": 1.315608735702322,
            "unit": "iter/sec",
            "range": "stddev: 0.08693691742978843",
            "extra": "mean: 760.1044085999945 msec\nrounds: 5"
          },
          {
            "name": "repository/tests/test_benchmark.py::test_benchmark_api_satellite_observations",
            "value": 3.475500432493763,
            "unit": "iter/sec",
            "range": "stddev: 0.04800296909847238",
            "extra": "mean: 287.72834859999534 msec\nrounds: 5"
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
            "email": "michelle.dadighat@noirlab.edu",
            "name": "Michelle Dadighat",
            "username": "mdadighat"
          },
          "distinct": true,
          "id": "7aa17275348628015cf00c02e61eff12f4039485",
          "message": "Add space to Planet Labs name",
          "timestamp": "2025-12-03T14:06:27-08:00",
          "tree_id": "9b3bb9f7b29456c21bf42419e63dc38507c3dd2f",
          "url": "https://github.com/iausathub/score/commit/7aa17275348628015cf00c02e61eff12f4039485"
        },
        "date": 1764799904345,
        "tool": "pytest",
        "benches": [
          {
            "name": "repository/tests/test_benchmark.py::test_benchmark_satellite_query",
            "value": 56.938508931466,
            "unit": "iter/sec",
            "range": "stddev: 0.007408408402404527",
            "extra": "mean: 17.56280624074033 msec\nrounds: 54"
          },
          {
            "name": "repository/tests/test_benchmark.py::test_benchmark_view_satellite_observations",
            "value": 173.00741582510278,
            "unit": "iter/sec",
            "range": "stddev: 0.005554743049089893",
            "extra": "mean: 5.780099050846024 msec\nrounds: 59"
          },
          {
            "name": "repository/tests/test_benchmark.py::test_benchmark_api_observations",
            "value": 1.7653244229548082,
            "unit": "iter/sec",
            "range": "stddev: 0.07765449069106281",
            "extra": "mean: 566.4681160000015 msec\nrounds: 5"
          },
          {
            "name": "repository/tests/test_benchmark.py::test_benchmark_api_satellite_observations",
            "value": 5.049623610650373,
            "unit": "iter/sec",
            "range": "stddev: 0.06397129132332828",
            "extra": "mean: 198.03456199999894 msec\nrounds: 6"
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
          "id": "eb63a96f3f95152691e4cff84339fdfa89f72e4b",
          "message": "Search location fix for missing results (#115)\n\n* Make sure filter_observations always returns a QuerySet when adding location to the search\n\n* Fix comment",
          "timestamp": "2025-12-05T10:46:23-08:00",
          "tree_id": "1f00ffe7641ec649e380ba3e748152a9802504f4",
          "url": "https://github.com/iausathub/score/commit/eb63a96f3f95152691e4cff84339fdfa89f72e4b"
        },
        "date": 1764960467126,
        "tool": "pytest",
        "benches": [
          {
            "name": "repository/tests/test_benchmark.py::test_benchmark_satellite_query",
            "value": 60.503215163043755,
            "unit": "iter/sec",
            "range": "stddev: 0.009198349252403181",
            "extra": "mean: 16.52804726666517 msec\nrounds: 60"
          },
          {
            "name": "repository/tests/test_benchmark.py::test_benchmark_view_satellite_observations",
            "value": 211.14420700257529,
            "unit": "iter/sec",
            "range": "stddev: 0.00022748537230366002",
            "extra": "mean: 4.73609962686688 msec\nrounds: 67"
          },
          {
            "name": "repository/tests/test_benchmark.py::test_benchmark_api_observations",
            "value": 1.3250246215744013,
            "unit": "iter/sec",
            "range": "stddev: 0.058109380402374206",
            "extra": "mean: 754.702956999995 msec\nrounds: 5"
          },
          {
            "name": "repository/tests/test_benchmark.py::test_benchmark_api_satellite_observations",
            "value": 3.607380935730002,
            "unit": "iter/sec",
            "range": "stddev: 0.01834347277291046",
            "extra": "mean: 277.2094263999975 msec\nrounds: 5"
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
          "id": "0a574a2e12276b7dffeeaa622d98e2cad23ffbf9",
          "message": "Remove SatChecker reference data from fields used to check for duplicate observations (#116)",
          "timestamp": "2025-12-23T09:09:36-08:00",
          "tree_id": "5380d5470f08e5a7ff43b49ab89f82876b20f793",
          "url": "https://github.com/iausathub/score/commit/0a574a2e12276b7dffeeaa622d98e2cad23ffbf9"
        },
        "date": 1766509853246,
        "tool": "pytest",
        "benches": [
          {
            "name": "repository/tests/test_benchmark.py::test_benchmark_satellite_query",
            "value": 55.45433570883138,
            "unit": "iter/sec",
            "range": "stddev: 0.009570527694233744",
            "extra": "mean: 18.03285509090942 msec\nrounds: 55"
          },
          {
            "name": "repository/tests/test_benchmark.py::test_benchmark_view_satellite_observations",
            "value": 199.36516425716601,
            "unit": "iter/sec",
            "range": "stddev: 0.00011841109156037602",
            "extra": "mean: 5.01592143103835 msec\nrounds: 58"
          },
          {
            "name": "repository/tests/test_benchmark.py::test_benchmark_api_observations",
            "value": 1.7044264559450315,
            "unit": "iter/sec",
            "range": "stddev: 0.09131448195435055",
            "extra": "mean: 586.7076262000069 msec\nrounds: 5"
          },
          {
            "name": "repository/tests/test_benchmark.py::test_benchmark_api_satellite_observations",
            "value": 1.9616704602764705,
            "unit": "iter/sec",
            "range": "stddev: 0.0803061403619983",
            "extra": "mean: 509.7696173999907 msec\nrounds: 5"
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
            "email": "michelle.dadighat@noirlab.edu",
            "name": "Michelle Dadighat",
            "username": "mdadighat"
          },
          "distinct": true,
          "id": "b05bdf2e6f5b243e91d3ccdd595ac300a67cd6b7",
          "message": "Move magnitude color bar down to avoid overlapping legend, and fix for Planet Labs satellites showing up as Other in all-sky plot legend",
          "timestamp": "2025-12-23T11:05:30-08:00",
          "tree_id": "7fcb1bcf78599f2561c3e689e6d5c264cab4847f",
          "url": "https://github.com/iausathub/score/commit/b05bdf2e6f5b243e91d3ccdd595ac300a67cd6b7"
        },
        "date": 1766516814387,
        "tool": "pytest",
        "benches": [
          {
            "name": "repository/tests/test_benchmark.py::test_benchmark_satellite_query",
            "value": 53.45862438257528,
            "unit": "iter/sec",
            "range": "stddev: 0.011839340164588905",
            "extra": "mean: 18.70605560000058 msec\nrounds: 55"
          },
          {
            "name": "repository/tests/test_benchmark.py::test_benchmark_view_satellite_observations",
            "value": 197.6114900277926,
            "unit": "iter/sec",
            "range": "stddev: 0.0001400583090138505",
            "extra": "mean: 5.060434491230026 msec\nrounds: 57"
          },
          {
            "name": "repository/tests/test_benchmark.py::test_benchmark_api_observations",
            "value": 0.9393103899777193,
            "unit": "iter/sec",
            "range": "stddev: 0.05014438279194297",
            "extra": "mean: 1.0646108151999898 sec\nrounds: 5"
          },
          {
            "name": "repository/tests/test_benchmark.py::test_benchmark_api_satellite_observations",
            "value": 0.9956878856582289,
            "unit": "iter/sec",
            "range": "stddev: 0.053426428846998504",
            "extra": "mean: 1.0043307891999915 sec\nrounds: 5"
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
            "email": "michelle.dadighat@noirlab.edu",
            "name": "Michelle Dadighat",
            "username": "mdadighat"
          },
          "distinct": true,
          "id": "8f4e54146827c29b367bb9e75c9c87ca4e180ed0",
          "message": "Make data visualization satellite selector and graph colors match, and match the ones on the main visualization page",
          "timestamp": "2025-12-27T17:53:48-08:00",
          "tree_id": "603851814936a9e1299228a665db7ef9c1e2d4a1",
          "url": "https://github.com/iausathub/score/commit/8f4e54146827c29b367bb9e75c9c87ca4e180ed0"
        },
        "date": 1766886909309,
        "tool": "pytest",
        "benches": [
          {
            "name": "repository/tests/test_benchmark.py::test_benchmark_satellite_query",
            "value": 53.91153209233321,
            "unit": "iter/sec",
            "range": "stddev: 0.010130427523575592",
            "extra": "mean: 18.54890709259236 msec\nrounds: 54"
          },
          {
            "name": "repository/tests/test_benchmark.py::test_benchmark_view_satellite_observations",
            "value": 196.1733320457917,
            "unit": "iter/sec",
            "range": "stddev: 0.00011941368749539765",
            "extra": "mean: 5.097532827584206 msec\nrounds: 58"
          },
          {
            "name": "repository/tests/test_benchmark.py::test_benchmark_api_observations",
            "value": 2.422405950430543,
            "unit": "iter/sec",
            "range": "stddev: 0.01753086963046279",
            "extra": "mean: 412.8127243999984 msec\nrounds: 5"
          },
          {
            "name": "repository/tests/test_benchmark.py::test_benchmark_api_satellite_observations",
            "value": 2.480980543888113,
            "unit": "iter/sec",
            "range": "stddev: 0.027410708646820818",
            "extra": "mean: 403.0664417999958 msec\nrounds: 5"
          }
        ]
      }
    ]
  }
}