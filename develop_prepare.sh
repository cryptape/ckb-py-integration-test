set -e
# git clone https://github.com/nervosnetwork/ckb-cli.git
# cd ckb-cli
# git checkout pkg/v1.7.0
# make prod
# cp target/release/ckb-cli ../source/ckb-cli
# cd ../
DEFAULT_BRANCH="develop"
DEFAULT_URL="https://github.com/nervosnetwork/ckb.git"

GitBranch="${GitBranch:-$DEFAULT_BRANCH}"
GitUrl="${GitUrl:-$DEFAULT_URL}"

cp download/0.110.2/ckb-cli ./source/ckb-cli-old
cp download/0.117.0/ckb-cli ./source/ckb-cli
git clone -b $GitBranch $GitUrl
cd ckb
make prod
cp target/prod/ckb ../download/0.117.0/ckb
