{
  description = "Environment for the BSc of Emanuel Prader";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs";
  };

  outputs = { nixpkgs, ... }:
    let
      system = "x86_64-linux";
      pkgs = import nixpkgs { inherit system; config.allowUnfree = true; };

    in
    {
      devShells.${system} = {
        default = pkgs.mkShell {
          buildInputs = with pkgs; [
            openssh
            ansible
            # glibcLocales

            kubectl
            kubernetes-helm
          ];

          shellHook = ''
            export PROJECT_ROOT=$PWD
            # NOTE:
            # To make the use of `ssh` with this projects custom config easier,
            # a small ssh wrapper script in `nix/scripts` is prepended to the $PATH
            # to prioritise it over the regular `ssh` command.
            export PATH=$PROJECT_ROOT/nix/scripts:$PATH
            export PS1="(nix-shell) $PS1" # NOTE: To communicate that a nix shell is active
            export KUBECONFIG=$PROJECT_ROOT/.kube/config
          '';
        };
      };
    };
}
