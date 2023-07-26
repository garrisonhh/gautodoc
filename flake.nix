{
  inputs = {
    nixpkgs.url = github:NixOs/nixpkgs/nixos-23.05;
  };

  outputs = { self, nixpkgs }:
    let
      # environment
      system = "x86_64-linux";

      # project reqs
      pkgs = (import (nixpkgs)) {
        inherit system;
      };
      inherit (pkgs) mkShell;
      pyPkgs = pkgs.python311Packages;
      libstdcpp = pkgs.stdenv.cc.cc.lib;

      # developer shell
      devShell = mkShell {
        packages = [
          pyPkgs.python
          libstdcpp
        ];

        shellHook = ''
          LD_LIBRARY_PATH="${libstdcpp}:$LD_LIBRARY_PATH"
        '';
      };
    in {
      devShells.${system}.default = devShell;
    };
}