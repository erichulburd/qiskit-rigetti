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
from typing import Optional, Any, Union, List

import pytest
from pyquil import get_qc, Program
from pyquil.api import QuantumComputer
from pytest_mock import MockerFixture
from qiskit import QuantumRegister, ClassicalRegister
from qiskit.providers import JobStatus

from qiskit_rigetti_provider import RigettiQCSJob, RigettiQCSProvider, RigettiQCSBackend, QuilCircuit
from qiskit_rigetti_provider.hooks.pre_compilation import PreCompilationHook
from qiskit_rigetti_provider.hooks.pre_execution import PreExecutionHook, enable_active_reset


def test_init__start_circuit_unsuccessful(backend: RigettiQCSBackend):
    circuit = make_circuit(2 * backend.configuration().num_qubits)  # Use too many qubits
    with pytest.raises(Exception):
        make_job(backend, circuit)


def test_init__before_compile_hook(backend: RigettiQCSBackend, mocker: MockerFixture):
    circuit = make_circuit(backend.configuration().num_qubits)
    qc = get_qc(backend.configuration().backend_name)
    quil_to_native_quil_spy = mocker.spy(qc.compiler, "quil_to_native_quil")

    new_qasm = "\n".join(
        [
            "OPENQASM 2.0;",
            'include "qelib1.inc";',
            "qreg q[2];",
            "creg ro[2];",
            "measure q[0] -> ro[0];",
            "measure q[1] -> ro[1];",
        ]
    )

    def before_compile(qasm: str) -> str:
        assert qasm.rstrip() == "\n".join(
            [
                "OPENQASM 2.0;",
                'include "qelib1.inc";',
                "qreg q[2];",
                "creg ro[2];",
                "h q[0];",
                "measure q[0] -> ro[0];",
                "measure q[1] -> ro[1];",
            ]
        )
        return new_qasm

    make_job(backend, circuit, qc, before_compile=before_compile)

    program: Program = quil_to_native_quil_spy.call_args[0][0]
    qasm = program.out(calibrations=False).rstrip()
    assert qasm == new_qasm


def test_init__multiple_before_compile_hooks(backend: RigettiQCSBackend, mocker: MockerFixture):
    circuit = make_circuit(backend.configuration().num_qubits)
    qc = get_qc(backend.configuration().backend_name)
    quil_to_native_quil_spy = mocker.spy(qc.compiler, "quil_to_native_quil")

    new_qasm_1 = "\n".join(
        [
            "OPENQASM 2.0;",
            'include "qelib1.inc";',
            "qreg q[2];",
            "creg ro[2];",
            # "h q[0];",  REMOVED
            "measure q[0] -> ro[0];",
            "measure q[1] -> ro[1];",
        ]
    )

    new_qasm_2 = "\n".join(
        [
            "OPENQASM 2.0;",
            'include "qelib1.inc";',
            "qreg q[2];",
            "creg ro[2];",
            "creg x[2];",  # ADDED
            "measure q[0] -> ro[0];",
            "measure q[1] -> ro[1];",
        ]
    )

    def before_compile_1(qasm: str) -> str:
        assert qasm.rstrip() == "\n".join(
            [
                "OPENQASM 2.0;",
                'include "qelib1.inc";',
                "qreg q[2];",
                "creg ro[2];",
                "h q[0];",
                "measure q[0] -> ro[0];",
                "measure q[1] -> ro[1];",
            ]
        )
        return new_qasm_1

    def before_compile_2(qasm: str) -> str:
        assert qasm.rstrip() == new_qasm_1
        return new_qasm_2

    make_job(backend, circuit, qc, before_compile=[before_compile_1, before_compile_2])

    program: Program = quil_to_native_quil_spy.call_args[0][0]
    qasm = program.out(calibrations=False).rstrip()
    assert qasm == new_qasm_2


def test_init__before_execute_hook(backend: RigettiQCSBackend, mocker: MockerFixture):
    circuit = make_circuit(backend.configuration().num_qubits)
    qc = get_qc(backend.configuration().backend_name)
    native_quil_to_executable_spy = mocker.spy(qc.compiler, "native_quil_to_executable")

    new_quil = Program(
        "DECLARE x BIT[1]",
    )

    def before_execute(quil: Program) -> Program:
        assert quil == Program(
            "DECLARE ro BIT[2]",
            "RZ(pi) 0",
            "RX(pi/2) 0",
            "RZ(pi/2) 0",
            "RX(-pi/2) 0",
            "MEASURE 1 ro[1]",
            "MEASURE 0 ro[0]",
        )
        return new_quil

    make_job(backend, circuit, qc, before_execute=before_execute)

    program: Program = native_quil_to_executable_spy.call_args[0][0]
    assert program == new_quil


def test_init__multiple_before_execute_hooks(backend: RigettiQCSBackend, mocker: MockerFixture):
    circuit = make_circuit(backend.configuration().num_qubits)
    qc = get_qc(backend.configuration().backend_name)
    native_quil_to_executable_spy = mocker.spy(qc.compiler, "native_quil_to_executable")

    new_quil_1 = Program(
        "DECLARE x BIT[1]",
    )

    new_quil_2 = Program(
        "DECLARE x BIT[1]",
        "DECLARE y BIT[1]",
    )

    def before_execute_1(quil: Program) -> Program:
        assert quil == Program(
            "DECLARE ro BIT[2]",
            "RZ(pi) 0",
            "RX(pi/2) 0",
            "RZ(pi/2) 0",
            "RX(-pi/2) 0",
            "MEASURE 1 ro[1]",
            "MEASURE 0 ro[0]",
        )
        return new_quil_1

    def before_execute_2(quil: Program) -> Program:
        assert quil == new_quil_1
        return new_quil_2

    make_job(backend, circuit, qc, before_execute=[before_execute_1, before_execute_2])

    program: Program = native_quil_to_executable_spy.call_args[0][0]
    assert program == new_quil_2


def test_init__ensure_native_quil__true(backend: RigettiQCSBackend, mocker: MockerFixture):
    circuit = make_circuit(backend.configuration().num_qubits)
    qc = get_qc(backend.configuration().backend_name)
    quil_to_native_quil_spy = mocker.spy(qc.compiler, "quil_to_native_quil")

    make_job(backend, circuit, qc, before_execute=enable_active_reset, ensure_native_quil=True)

    assert quil_to_native_quil_spy.call_count == 2, "compile not performed correct number of times"


def test_init__ensure_native_quil__ignored_if_no_pre_execution_hooks(backend: RigettiQCSBackend, mocker: MockerFixture):
    circuit = make_circuit(backend.configuration().num_qubits)
    qc = get_qc(backend.configuration().backend_name)
    quil_to_native_quil_spy = mocker.spy(qc.compiler, "quil_to_native_quil")

    make_job(backend, circuit, qc, ensure_native_quil=True)

    assert quil_to_native_quil_spy.call_count == 1, "compile not performed correct number of times"


def test_init__ensure_native_quil__false(backend: RigettiQCSBackend, mocker: MockerFixture):
    circuit = make_circuit(backend.configuration().num_qubits)
    qc = get_qc(backend.configuration().backend_name)
    quil_to_native_quil_spy = mocker.spy(qc.compiler, "quil_to_native_quil")

    make_job(backend, circuit, qc, ensure_native_quil=False)

    assert quil_to_native_quil_spy.call_count == 1, "compile not performed correct number of times"


def test_result(job: RigettiQCSJob):
    result = job.result()

    assert result.date == job.result().date, "Result not cached"

    assert job.status() == JobStatus.DONE

    assert result.backend_name == "2q-qvm"
    assert result.job_id == job.job_id()
    assert result.success is True

    result_0 = result.results[0]
    assert result_0.success is True
    assert result_0.status == "Completed successfully"
    assert result_0.shots == 1000
    assert len(result_0.data.memory) == 1000

    # Note: this can flake if number of shots is not large enough -- 1000 should be enough
    assert result_0.data.counts.keys() == {"00", "01"}


def test_cancel(job: RigettiQCSJob):
    with pytest.raises(NotImplementedError, match="Cancelling jobs is not supported"):
        job.cancel()


def test_submit(job: RigettiQCSJob):
    with pytest.raises(
            NotImplementedError,
            match="'submit' is not implemented as this class uses the asynchronous pattern",
    ):
        job.submit()


@pytest.fixture
def backend():
    return RigettiQCSProvider().get_simulator(num_qubits=2)


@pytest.fixture
def job(backend):
    circuit = make_circuit(backend.configuration().num_qubits)
    return make_job(backend, circuit)


def make_circuit(num_qubits) -> QuilCircuit:
    circuit = QuilCircuit(QuantumRegister(num_qubits, "q"), ClassicalRegister(num_qubits, "ro"))
    circuit.h(0)
    circuit.measure(range(num_qubits), range(num_qubits))
    return circuit


def make_job(
        backend,
        circuit,
        qc: Optional[QuantumComputer] = None,
        before_compile: Optional[Union[PreCompilationHook, List[PreCompilationHook]]] = None,
        before_execute: Optional[Union[PreExecutionHook, List[PreExecutionHook]]] = None,
        ensure_native_quil: bool = False,
        **options: Any,
):
    qc = qc or get_qc(backend.configuration().backend_name)
    job = RigettiQCSJob(
        job_id="some_job",
        circuits=[circuit],
        options={**{"shots": 1000}, **options},
        qc=qc,
        backend=backend,
        configuration=backend.configuration(),
        before_compile=before_compile or [],
        before_execute=before_execute or [],
        ensure_native_quil=ensure_native_quil,
    )

    return job
