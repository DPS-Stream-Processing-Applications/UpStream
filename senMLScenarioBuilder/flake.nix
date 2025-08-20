{
  description = "A tool to replace the original timestamps of the senML datasets with a custom scenario timeline.";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs";
  };

  outputs = { nixpkgs, ... }:
    let
      system = "x86_64-linux";
      pkgs = import nixpkgs { inherit system; };

    in
    {
      devShells.${system} = {
        default = pkgs.mkShell {
          buildInputs = with pkgs; [
            poetry
          ];

          env = {
            # NOTE: Adding `(nix-shell)` as a visual marker when a Nix dev shell is active.
            PS1 = "(nix-shell) $PS1";
            # INFO:
            # Some python packages depend on dynamic libraries to be available via the linker.
            # In Nix, these libraries do not live in the expected directories.
            # Therefore, if one wants to make these libraries available one needs to add them manually.
            LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
              pkgs.stdenv.cc.cc.lib
              pkgs.libz
            ];
          };
        };
      };
    };
}
