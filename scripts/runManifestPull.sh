#!/usr/bin/env bash
#
# Copyright 2020-2021, Institute for Systems Biology
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

export MY_VENV=~/pyVenvForThree
export PYTHONPATH=.:${MY_VENV}/lib

TABLE='your-project-id.your-dataset.your-manifest-table' # BQ table with your manifest
TARG_DIR='/path-to-your-home-dir/destination' # Has to be on a filesystem with enough sapce
PAYING='your-project-id' # Needed for requester pays though it is free to crossload to a cloud VM

cd ~
pushd ${MY_VENV} > /dev/null
source bin/activate
popd > /dev/null
python3 ~/IDC-Examples/scripts/pullManifestToVM.py --table ${TABLE} --destination ${TARG_DIR} --paying ${PAYING}
deactivate
