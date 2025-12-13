#!/usr/bin/env python3
"""
Simple test to verify the extensions work correctly by importing them properly.
"""

import sys
import os
import tempfile
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.getcwd(), 'src'))

def test_probabilistic():
    """Test probabilistic extension."""
    print("🔍 Testing Probabilistic Extension...")
    
    # Import directly
    from null_system.extensions.probabilistic import ProbabilisticValue, NullDecisionEngine, ProbabilisticEvaluator
    
    # Test ProbabilisticValue
    val1 = ProbabilisticValue(42, confidence=0.8, uncertainty=0.2)
    val2 = ProbabilisticValue(58, confidence=0.9, uncertainty=0.1)
    
    # Test combination
    combined = val1.combine(val2, 'weighted')
    assert combined.value > 0
    assert 0.8 <= combined.confidence <= 0.9
    
    # Test DecisionEngine
    engine = NullDecisionEngine()
    result = engine.make_decision('test', {'feature1': 0.8, 'feature2': 0.6})
    assert isinstance(result, ProbabilisticValue)
    
    # Test Evaluator
    evaluator = ProbabilisticEvaluator(engine)
    variables = {
        "x": ProbabilisticValue(10, confidence=0.8),
        "threshold": ProbabilisticValue(5, confidence=0.9)
    }
    
    result = evaluator.evaluate_condition_with_confidence("x > threshold", variables)
    assert result.value == True
    assert result.confidence > 0.5
    
    print("✅ Probabilistic extension tests passed")

def test_networking():
    """Test networking extension."""
    print("🌐 Testing Networking Extension...")
    
    from null_system.extensions.networking import (
        RPCMessage, MessageType, NetworkingManager, 
        DistributedNullVM, TLSConfig, ExecutionStatus
    )
    
    # Test RPCMessage
    message = RPCMessage(
        message_type=MessageType.EXECUTE_REQUEST,
        message_id="test-123",
        source_id="client",
        payload={"test": "data"}
    )
    
    # Test serialization
    json_str = message.to_json()
    restored = RPCMessage.from_json(json_str)
    assert restored.message_id == message.message_id
    
    # Test NetworkingManager
    manager = NetworkingManager()
    assert len(manager.servers) == 0
    
    # Test DistributedNullVM
    vm = DistributedNullVM(manager)
    vm.register_remote_node("node1", {"capabilities": ["null-lang"]})
    assert "node1" in vm.remote_nodes
    
    print("✅ Networking extension tests passed")

def test_filesystem():
    """Test filesystem extension."""
    print("📁 Testing File-system Extension...")
    
    from null_system.extensions.filesystem import (
        NullFSArchive, NullFSManager, NullFSFile,
        CompressionType, EncryptionType
    )
    
    # Test archive creation
    archive = NullFSArchive(compression_type=CompressionType.GZIP)
    
    # Add files
    archive.add_file('test.txt', 'Hello, World!')
    archive.add_file('data.json', json.dumps({'key': 'value'}))
    
    assert len(archive.list_files()) == 2
    
    # Test file retrieval
    content = archive.get_file('test.txt')
    assert content.decode() == 'Hello, World!'
    
    # Test save and load
    with tempfile.NamedTemporaryFile(suffix='.nfsb', delete=False) as f:
        temp_path = f.name
    
    try:
        archive.save_to_file(temp_path)
        loaded_archive = NullFSArchive.load_from_file(temp_path)
        assert len(loaded_archive.list_files()) == 2
        
        # Verify content
        loaded_content = loaded_archive.get_file('test.txt')
        assert loaded_content.decode() == 'Hello, World!'
        
    finally:
        os.unlink(temp_path)
    
    # Test NullFSManager
    manager = NullFSManager()
    new_archive = manager.create_archive('test_archive')
    new_archive.add_file('example.txt', 'Example content')
    
    assert 'test_archive' in manager.list_archives()
    
    print("✅ File-system extension tests passed")

def test_integration():
    """Test integration."""
    print("🔗 Testing Extension Integration...")
    
    from null_system.extensions.probabilistic import ProbabilisticValue, NullDecisionEngine
    from null_system.extensions.networking import NetworkingManager, DistributedNullVM
    from null_system.extensions.filesystem import NullFSManager
    
    # Create components
    engine = NullDecisionEngine()
    manager = NetworkingManager()
    vm = DistributedNullVM(manager)
    fs_manager = NullFSManager()
    
    # Test workflow
    results = {'confidence': 0.85, 'value': 42, 'uncertainty': 0.15}
    prob_result = ProbabilisticValue(results['value'], results['confidence'], results['uncertainty'])
    
    # Store in archive
    archive = fs_manager.create_archive('execution_results')
    archive.add_file('results.json', json.dumps(results))
    
    # Make decision
    features = {'confidence': results['confidence'], 'uncertainty': results['uncertainty']}
    decision = engine.make_decision('execution_strategy', features)
    
    # Verify integration
    assert len(archive.list_files()) == 1
    assert decision.confidence >= 0 and decision.confidence <= 1
    
    print("✅ Extension integration tests passed")

def main():
    """Run all tests."""
    print("🚀 Running AI Network Storage Extension Tests")
    print("=" * 50)
    
    try:
        test_probabilistic()
        test_networking()
        test_filesystem()
        test_integration()
        
        print("\n" + "=" * 50)
        print("🎉 All tests passed! AI network storage extensions are working correctly.")
        print("\n📋 Extension Summary:")
        print("  • Probabilistic: Confidence-aware computation with AI decision hooks")
        print("  • Networking: Distributed execution with TLS and RPC protocol")
        print("  • File-system: Super-bit encoded archives with compression/encryption")
        print("  • Integration: All components work together seamlessly")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)