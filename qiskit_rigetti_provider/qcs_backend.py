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
import warnings
from typing import Optional, Any, Union, List
from uuid import uuid4

from pyquil import get_qc
from pyquil.api import QuantumComputer, EngagementManager
from qcs_api_client.client import QCSClientConfiguration
from qiskit import QuantumCircuit, ClassicalRegister
from qiskit.circuit import Barrier, Measure, Clbit
from qiskit.providers import BackendV1, Options, Provider
from qiskit.providers.models import QasmBackendConfiguration

from .qcs_job import RigettiQCSJob


def _remove_barriers(circuit: QuantumCircuit) -> None:
    """Strips barriers from the circuit. Mutates the input circuit."""
    data = []
    for d in circuit.data:
        if isinstance(d[0], Barrier):
            warnings.warn("`barrier` has no effect on a RigettiQCSBackend and will be omitted")
        else:
            data.append(d)
    circuit.data = data


def _prepare_readouts(circuit: QuantumCircuit) -> None:
    """
    Errors if measuring into more than one readout. If only measuring one, ensures its name is 'ro'. Mutates the input
    circuit.
    """
    measures = [d for d in circuit.data if isinstance(d[0], Measure)]
    readout_names = list({clbit.register.name for m in measures for clbit in m[2]})

    if len(readout_names) > 1:
        readout_names.sort()
        raise RuntimeError(
            f"Multiple readout registers are unsupported on QCSBackend; found {', '.join(readout_names)}"
        )
    elif len(readout_names) == 1:
        name = readout_names[0]
        if name != "ro":
            # Rename register to "ro"
            for i, reg in enumerate(circuit.cregs):
                if reg.name == name:
                    circuit.cregs[i] = ClassicalRegister(size=reg.size, name="ro")

            # Rename register references to "ro"
            for m in measures:
                for i, clbit in enumerate(m[2]):
                    if clbit.register.name == name:
                        m[2][i] = Clbit(
                            register=ClassicalRegister(size=clbit.register.size, name="ro"),
                            index=clbit.index,
                        )
            for i, clbit in enumerate(circuit.clbits):
                if clbit.register.name == name:
                    circuit.clbits[i] = Clbit(
                        register=ClassicalRegister(size=clbit.register.size, name="ro"),
                        index=clbit.index,
                    )


def _prepare_circuit(circuit: QuantumCircuit) -> QuantumCircuit:
    """
    Returns a prepared copy of the circuit for execution on the QCS Backend.
    """
    circuit = circuit.copy()
    _remove_barriers(circuit)
    _prepare_readouts(circuit)
    return circuit


class RigettiQCSBackend(BackendV1):
    """
    Class for representing a Rigetti backend, which may target a real QPU or a simulator.
    """

    def __init__(
        self,
        *,
        compiler_timeout: float = 5.0,
        execution_timeout: float = 5.0,
        client_configuration: QCSClientConfiguration,
        engagement_manager: EngagementManager,
        backend_configuration: QasmBackendConfiguration,
        provider: Optional[Provider],
        **fields: Any,
    ) -> None:
        """
        Create a new backend.

        :param execution_timeout: Time limit for execution requests, in seconds.
        :param compiler_timeout: Time limit for compiler requests, in seconds.
        :param client_configuration: QCS client configuration.
        :param engagement_manager: QPU engagement manager.
        :param backend_configuration: Backend configuration.
        :param provider: Parent provider.
        :param fields: kwargs for the values to use to override the default options.
        """
        super().__init__(backend_configuration, provider, **fields)
        self._compiler_timeout = compiler_timeout
        self._execution_timeout = execution_timeout
        self._client_configuration = client_configuration
        self._engagement_manager = engagement_manager
        self._qc: Optional[QuantumComputer] = None

    @classmethod
    def _default_options(cls) -> Options:
        return Options(shots=None)

    def run(self, run_input: Union[QuantumCircuit, List[QuantumCircuit]], **options: Any) -> RigettiQCSJob:
        if not isinstance(run_input, list):
            run_input = [run_input]

        run_input = [_prepare_circuit(circuit) for circuit in run_input]

        if self._qc is None:
            self._qc = get_qc(
                self.configuration().backend_name,
                compiler_timeout=self._compiler_timeout,
                execution_timeout=self._execution_timeout,
                client_configuration=self._client_configuration,
                engagement_manager=self._engagement_manager,
            )

        job = RigettiQCSJob(
            job_id=str(uuid4()),
            circuits=run_input,
            options=options,
            qc=self._qc,
            backend=self,
            configuration=self.configuration(),
        )
        return job