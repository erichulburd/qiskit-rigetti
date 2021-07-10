##############################################################################
# Copyright 2021 Rigetti Computing
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
##############################################################################
import sys

from .quil_circuit import QuilCircuit
from .qcs_backend import RigettiQCSBackend
from .qcs_job import RigettiQCSJob
from .qcs_provider import RigettiQCSProvider

if sys.version_info < (3, 8):
    from importlib_metadata import version  # pragma: nocover
else:
    from importlib.metadata import version  # pragma: nocover

__version__ = version(__package__)  # type: ignore