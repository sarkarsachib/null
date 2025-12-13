#!/usr/bin/env python3
"""
Test script to validate the AI network storage extensions implementation.
This tests all three extensions (probabilistic, networking, filesystem) working together.
"""

import sys
import os
import tempfile
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.getcwd(), 'src'))

def test_probabilistic_extension():
    """Test the probabilistic extension functionality."""
    print("\n🔍 Testing Probabilistic Extension...")
    
    # Load probabilistic extension
    exec(open('/home/engine/project/src/null_system/extensions/probabilistic.py').read())
    
    # Test ProbabilisticValue
    val1 = ProbabilisticValue(42, confidence=0.8, uncertainty=0.2)
    val2 = ProbabilisticValue(58, confidence=0.9, uncertainty=0.1)
    
    # Test combination
    combined = val1.combine(val2, 'weighted')
    assert combined.value == 50.0  # (42*0.8 + 58*0.9) / (0.8+0.9) = 50.47...
    assert 0.8 <= combined.confidence <= 0.9
    
    # Test NullDecisionEngine
    engine = NullDecisionEngine()
    
    # Add decision hook
    def test_hook(context, features):
        if context == "test_high_confidence":
            return ProbabilisticValue(True, confidence=0.95)
        return None
    
    engine.add_decision_hook(test_hook)
    
    # Test heuristic decision
    result1 = engine.make_decision('test_context', {'feature1': 0.8, 'feature2': 0.6})
    assert isinstance(result1, ProbabilisticValue)
    
    # Test hook-based decision
    result2 = engine.make_decision('test_high_confidence', {'feature1': 0.8})
    assert result2.confidence == 0.95
    
    # Test ProbabilisticEvaluator
    evaluator = ProbabilisticEvaluator(engine)
    
    variables = {
        "x": ProbabilisticValue(10, confidence=0.8),
        "threshold": ProbabilisticValue(5, confidence=0.9)
    }
    
    result = evaluator.evaluate_condition_with_confidence("x > threshold", variables)
    assert result.value == True
    assert result.confidence > 0.5
    
    print("✅ Probabilistic extension tests passed")
    return True

def test_networking_extension():
    """Test the networking extension functionality."""
    print("\n🌐 Testing Networking Extension...")
    
    # Load networking extension
    exec(open('/home/engine/project/src/null_system/extensions/networking.py').read())
    
    # Test TLSConfig
    tls_config = TLSConfig(enabled=True, cert_path=Path("test.crt"))
    assert tls_config.enabled == True
    
    # Test RPCMessage
    message = RPCMessage(
        message_type=MessageType.EXECUTE_REQUEST,
        message_id="test-123",
        source_id="client",
        payload={"test": "data"}
    )
    
    assert message.message_type == MessageType.EXECUTE_REQUEST
    
    # Test serialization
    json_str = message.to_json()
    restored = RPCMessage.from_json(json_str)
    assert restored.message_id == message.message_id
    
    # Test ExecutionRequest/Response
    request = ExecutionRequest(
        program_source="print hello",
        program_id="prog-123"
    )
    
    response = ExecutionResponse(
        program_id="prog-123",
        status=ExecutionStatus.SUCCESS,
        output=["Hello!"],
        execution_time=0.5
    )
    
    assert response.status == ExecutionStatus.SUCCESS
    
    # Test NetworkingManager
    manager = NetworkingManager()
    assert len(manager.servers) == 0
    assert len(manager.clients) == 0
    
    # Test DistributedNullVM
    vm = DistributedNullVM(manager)
    vm.register_remote_node("node1", {"capabilities": ["null-lang"]})
    
    assert "node1" in vm.remote_nodes
    
    # Test load balancing
    vm.set_load_balancing_strategy("least_loaded")
    assert vm.load_balancing_strategy == "least_loaded"
    
    print("✅ Networking extension tests passed")
    return True

def test_filesystem_extension():
    """Test the filesystem extension functionality."""
    print("\n📁 Testing File-system Extension...")
    
    # Load filesystem extension
    exec(open('/home/engine/project/src/null_system/extensions/filesystem.py').read())
    
    # Test archive creation
    archive = NullFSArchive(compression_type=CompressionType.GZIP)
    
    # Add files
    archive.add_file('test.txt', 'Hello, World!')
    archive.add_file('data.json', json.dumps({'key': 'value', 'number': 42}))
    archive.add_file('binary.dat', b'\x00\x01\x02\x03\x04')
    
    assert len(archive.list_files()) == 3
    
    # Test file retrieval
    content = archive.get_file('test.txt')
    assert content.decode() == 'Hello, World!'
    
    # Test metadata
    info = archive.get_file_info('test.txt')
    assert info.path == 'test.txt'
    assert info.size == 13  # len('Hello, World!')
    
    # Test archive info
    archive_info = archive.get_archive_info()
    assert archive_info['total_files'] == 3
    
    # Test save and load
    with tempfile.NamedTemporaryFile(suffix='.nfsb', delete=False) as f:
        temp_path = f.name
    
    try:
        archive.save_to_file(temp_path)
        assert Path(temp_path).exists()
        
        # Load it back
        loaded_archive = NullFSArchive.load_from_file(temp_path)
        assert len(loaded_archive.list_files()) == 3
        
        # Verify content integrity
        loaded_content = loaded_archive.get_file('test.txt')
        assert loaded_content.decode() == 'Hello, World!'
        
        loaded_binary = loaded_archive.get_file('binary.dat')
        assert loaded_binary == b'\x00\x01\x02\x03\x04'
        
    finally:
        os.unlink(temp_path)
    
    # Test NullFSManager
    manager = NullFSManager()
    new_archive = manager.create_archive('test_archive', CompressionType.GZIP)
    new_archive.add_file('example.txt', 'Example content')
    
    assert 'test_archive' in manager.list_archives()
    
    # Test file operations
    with NullFSFile(archive, 'test.txt', 'r') as f:
        content = f.read()
        assert content == b'Hello, World!'
        
        # Test seeking
        pos = f.seek(6)
        assert pos == 6
        
        remaining = f.read()
        assert remaining == b'World!'
    
    print("✅ File-system extension tests passed")
    return True

def test_integration():
    """Test integration between all extensions."""
    print("\n🔗 Testing Extension Integration...")
    
    # Load all extensions
    exec(open('/home/engine/project/src/null_system/extensions/probabilistic.py').read())
    exec(open('/home/engine/project/src/null_system/extensions/networking.py').read())
    exec(open('/home/engine/project/src/null_system/extensions/filesystem.py').read())
    
    # Create probabilistic decision engine
    engine = NullDecisionEngine()
    evaluator = ProbabilisticEvaluator(engine)
    
    # Create networking manager
    manager = NetworkingManager()
    vm = DistributedNullVM(manager)
    
    # Create file system manager
    fs_manager = NullFSManager()
    
    # Simulate a workflow where:
    # 1. We have probabilistic program results
    # 2. Store them in archives
    # 3. Execute remotely with AI decisions
    
    # Step 1: Create probabilistic program results
    results = {
        'confidence': 0.85,
        'value': 42,
        'uncertainty': 0.15,
        'execution_time': 0.3
    }
    
    prob_result = ProbabilisticValue(results['value'], results['confidence'], results['uncertainty'])
    
    # Step 2: Store in archive
    archive = fs_manager.create_archive('execution_results')
    archive.add_file('results.json', json.dumps(results))
    
    # Step 3: Make AI decision about execution strategy
    features = {
        'confidence': results['confidence'],
        'uncertainty': results['uncertainty'],
        'execution_time': results['execution_time']
    }
    
    decision = engine.make_decision('execution_strategy', features)
    
    # Step 4: Store decision in archive
    decision_data = {
        'decision': decision.value,
        'confidence': decision.confidence,
        'strategy': 'distributed' if decision.confidence > 0.7 else 'local'
    }
    
    archive.add_file('decision.json', json.dumps(decision_data))
    
    # Verify the integrated workflow
    assert len(archive.list_files()) == 2
    
    # Retrieve and verify
    retrieved_results = json.loads(archive.get_file('results.json').decode())
    retrieved_decision = json.loads(archive.get_file('decision.json').decode())
    
    assert retrieved_results['value'] == 42
    assert retrieved_decision['strategy'] == 'distributed'
    
    print("✅ Extension integration tests passed")
    return True

def main():
    """Run all tests."""
    print("🚀 Running AI Network Storage Extension Tests")
    print("=" * 50)
    
    tests = [
        ("Probabilistic Extension", test_probabilistic_extension),
        ("Networking Extension", test_networking_extension), 
        ("File-system Extension", test_filesystem_extension),
        ("Extension Integration", test_integration)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
                print(f"❌ {test_name} failed")
        except Exception as e:
            failed += 1
            print(f"❌ {test_name} failed with error: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! AI network storage extensions are working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)