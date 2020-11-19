L1 Transceiver config will affect the line quality, it has 5 sub-parameters as below:
"preEmphasis" : {
            "range" : [-20, 20, 1] #[begin, end, step]
        },
        "mainTap" : {
            "range" : [-20, 20, 1]
        },
        "postEmphasis" : {
            "range" : [-20, 20, 1]
        },
        "txCoarseSwing" : {
            "range" : [0, 6, 1]
        },
        "ctle" : {
            "range" : [0, 63, 1]
        }
If we want to traverse all configs, there will be max 30876608 (41*41*41*7*64) instances. Each instance will take nearly 30s to test. So that it is impossible to do that. We must design a more effective algorithm to decrease instances.
