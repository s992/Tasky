INSTALL_DIR=$1

if [ -z "$INSTALL_DIR" ]; then
  INSTALL_DIR="$HOME/dotfiles/bin"
fi

bazel build tasky --build_python_zip
cp bazel-bin/tasky "$INSTALL_DIR"
