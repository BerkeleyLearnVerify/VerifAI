poetry install
python_path=$(which python)
site_packages_path=$(dirname $python_path)
rm -rf $site_packages_path/../lib/python3.8/site-packages/scenic*
cd ../../Scenic
poetry install
cd ../VerifAI/demo
