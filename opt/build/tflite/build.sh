#!/bin/bash
set -e
set -x

cd `dirname ${BASH_SOURCE[0]}`
ARCH=$1

VERSION=$2
if [ "X$VERSION" == "X" ]; then
    VERSION=2.4.0
fi

BASEOS=$3
if [ "X$BASEOS" == "X" ]; then
    BASEOS=linux
fi

if [ ! -f v$VERSION.tar.gz ]; then
    wget -q https://github.com/tensorflow/tensorflow/archive/v$VERSION.tar.gz
    tar -xzf v$VERSION.tar.gz
fi
cd tensorflow-$VERSION

# fetch dependencies
./tensorflow/lite/tools/make/download_dependencies.sh

# build tensorflow lite library
bazel build --config=monolithic --config=cuda //tensorflow/lite:libtensorflowlite.so
TMP_LIB="tmp"
# flatbuffer header files
mkdir -p $TMP_LIB/include
cp -r tensorflow/lite/tools/make/downloads/flatbuffers/include/flatbuffers $TMP_LIB/include/
# tensorflow lite header files
TFLITE_DIR="tensorflow/lite"
declare -a tfLiteDirectories=(
    "$TFLITE_DIR"
    "$TFLITE_DIR/c"
    "$TFLITE_DIR/core"
    "$TFLITE_DIR/core/api"
    "$TFLITE_DIR/delegates/nnapi"
    "$TFLITE_DIR/delegates/xnnpack"
    "$TFLITE_DIR/experimental/resource"
    "$TFLITE_DIR/kernels"
    "$TFLITE_DIR/nnapi"
    "$TFLITE_DIR/schema"
    "$TFLITE_DIR/tools/evaluation"
)
for dir in "${tfLiteDirectories[@]}"
do
    mkdir -p $TMP_LIB/include/$dir
    cp $dir/*h $TMP_LIB/include/$dir
done
mkdir -p $TMP_LIB/lib
cp bazel-bin/tensorflow/lite/libtensorflowlite.so $TMP_LIB/lib
bazel build -c opt --copt -DMESA_EGL_NO_X11_HEADERS --copt -DEGL_NO_X11 tensorflow/lite/delegates/gpu:libtensorflowlite_gpu_delegate.so
cp bazel-bin/tensorflow/lite/delegates/gpu/libtensorflowlite_gpu_delegate.so $TMP_LIB/lib
# create .tar.gz file
cd $TMP_LIB
tar -cvzf libtensorflowlite-$BASEOS-$ARCH-$VERSION.tar.gz include lib