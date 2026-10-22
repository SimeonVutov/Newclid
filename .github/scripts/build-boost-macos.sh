#!/usr/bin/env bash
set -euxo pipefail

BOOST_DIR_NAME="boost_${BOOST_VERSION//./_}"

curl -L "https://archives.boost.io/release/${BOOST_VERSION}/source/${BOOST_DIR_NAME}.tar.gz" -o boost.tar.gz
tar -xzf boost.tar.gz
cd "${BOOST_DIR_NAME}"

GCC_PREFIX="$(brew --prefix gcc@14)"
echo "using gcc : 14 : ${GCC_PREFIX}/bin/g++-14 ;" > "$HOME/user-config.jam"

./bootstrap.sh \
  --prefix="$GITHUB_WORKSPACE/${BOOST_INSTALL_DIR}" \
  --with-libraries=atomic,chrono,container,date_time,filesystem,json,log,program_options,regex,system,thread,test

./b2 \
  -j"$(sysctl -n hw.ncpu)" \
  toolset=gcc-14 \
  target-os=darwin \
  cxxstd=23 \
  variant=release \
  threading=multi \
  link=static \
  runtime-link=shared \
  install
