# Uroboros [\[1\]](#uroboros)
### Infrastructure for Reassembleable Disassembling and Transformation

### Fork motivation

This fork is made with the idea of extending this technique to ARM Thumb executables. In such process, the OCaml core has been completely rewritten in Python. To this date the tool has been tested to work on the following executables: bzip, gzip.

## Installation

Uroboros uses the following utilities (version numbers are in line with what was used during development, older releases may work as well):

| Tool        | Version |
|:------------|--------:|
| python      | 2.7     |
| objdump     | ≥2.22   |
| readelf     | ≥2.22   |
| awk         | ≥3.18   |
| libcapstone | ≥3.0.4  |

and the following python packages (available through `pip` repositories):

| Package     | Version |
|:------------|--------:|
| capstone    | ≥3.0.4  |
| termcolor   | ≥1.1.0  |
| ELF-Esteem  | ≥0.1    |

## Build

Uroboros is now completely written in Python on the `allpy` branch. You don't need to build anything. However, you may want to modify some value in `config.py` to match your system configuration.

## Usage: Disassembling

Uroboros supports 64-bit and 32-bit ELF x86 executables and, experimentally, also Thumb2 ARM binaries.
To use Uroboros for disassembling:

```bash
 $> python uroboros.py path_to_bin
```

The disassembled output can be found in the `workdir` directory, named `final.s`. Uroboros will also assemble it back into an executable, `a.out`.

The startup Python script provides the following options:

1. `-o (output)`

    This option allows to specify an output path for the reassembled binary.

2. `-g`

    **NOT YET DEVELOPED**

    Instrument the output binary against ROP attacks using an adaptation of the technique described in [\[2\]](#gfree).

3. `-a (assumption)`

    This option configures the three symbolization assumptions proposed in
    the original Uroboros paper [\[1\]](#uroboros). Note that in the current version, the
    first assumption (**n-byte alignment**) are set by default. The other
    two assumptions can be set by users.

    Assumption two reqires to put data sections (.data, .rodata and .bss)
    to its original starting addresses. Linker scripts can be used during
    reassembling (`gcc -T ld_script.sty final.s`). Users may write their
    own linker script, some examples are given at `ld_script` folder.

    Assumption three requires to know the function starting addresses. To
    obtain this information, Uroboros can take unstripped binaries
    as input. The function starting address information is obtained from
    the input, which is then stripped before disassembling.

    These assumptions can also be used at the same time (`python uroboros.py path_to_bin -a 3 -a 2`)



<a name="uroboros">[1]</a> [Reassembleable Disassembling](https://www.usenix.org/conference/usenixsecurity15/technical-sessions/presentation/wang-shuai), by Shuai Wang, Pei Wang, and Dinghao Wu. In Proceedings of the 24th USENIX Security Symposium, Washington, D.C., August 12-14. 2015.

<a name="gfree">[2]</a> [G-Free: defeating return-oriented programming through gadget-less binaries](https://doi.org/10.1145/1920261.1920269), by Onarlioglu Kaan, Leyla Bilge, Andrea Lanzi, Davide Balzarotti, and Engin Kirda. In Proceedings of the 26th Annual Computer Security Applications Conference, pp. 49-58. ACM, 2010."
