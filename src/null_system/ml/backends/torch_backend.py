"""PyTorch backend for ML models."""

from typing import Dict, List, Tuple, Any, Optional
import numpy as np

try:
    import torch
    import torch.nn as nn
    import torchvision.models as models
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


class TorchBackend:
    """PyTorch backend for model inference."""

    def __init__(self, device: str = "cpu"):
        """Initialize PyTorch backend.
        
        Args:
            device: Device to use ('cpu' or 'cuda')
        """
        if not TORCH_AVAILABLE:
            raise RuntimeError("PyTorch is not installed")
        
        self.device = torch.device(device)
        self.models = {}

    def load_model(self, model_name: str, pretrained: bool = True) -> nn.Module:
        """Load a model.
        
        Args:
            model_name: Model name (e.g., 'resnet18')
            pretrained: Whether to use pretrained weights
            
        Returns:
            Loaded model
        """
        if model_name in self.models:
            return self.models[model_name]
        
        if model_name == "resnet18":
            model = models.resnet18(pretrained=pretrained)
        elif model_name == "resnet50":
            model = models.resnet50(pretrained=pretrained)
        elif model_name == "mobilenet_v2":
            model = models.mobilenet_v2(pretrained=pretrained)
        else:
            raise ValueError(f"Unknown model: {model_name}")
        
        model = model.to(self.device)
        model.eval()
        
        self.models[model_name] = model
        return model

    def forward(
        self,
        model: nn.Module,
        input_data: np.ndarray,
    ) -> np.ndarray:
        """Run forward pass.
        
        Args:
            model: Model to run
            input_data: Input data
            
        Returns:
            Output array
        """
        with torch.no_grad():
            # Convert to tensor
            if isinstance(input_data, np.ndarray):
                tensor = torch.from_numpy(input_data).float()
            else:
                tensor = input_data
            
            tensor = tensor.to(self.device)
            
            # Forward pass
            output = model(tensor)
            
            # Convert back to numpy
            if isinstance(output, torch.Tensor):
                output = output.cpu().numpy()
            
            return output

    def get_model_size(self, model: nn.Module) -> int:
        """Get model size in bytes.
        
        Args:
            model: Model to measure
            
        Returns:
            Size in bytes
        """
        total_params = 0
        for param in model.parameters():
            total_params += param.numel() * param.element_size()
        
        return total_params

    def quantize_model(
        self,
        model: nn.Module,
        bits: int = 8,
    ) -> nn.Module:
        """Quantize model.
        
        Args:
            model: Model to quantize
            bits: Quantization bits
            
        Returns:
            Quantized model
        """
        # Simple quantization using dynamic quantization
        if TORCH_AVAILABLE and hasattr(torch.quantization, 'quantize_dynamic'):
            try:
                quantized = torch.quantization.quantize_dynamic(
                    model,
                    {nn.Linear, nn.Conv2d},
                    dtype=torch.qint8
                )
                return quantized
            except Exception:
                return model
        
        return model


class TorchInferenceEngine:
    """Inference engine using PyTorch."""

    def __init__(self, device: str = "cpu"):
        """Initialize engine.
        
        Args:
            device: Device to use
        """
        self.backend = TorchBackend(device=device)
        self.loaded_models = {}

    def load_resnet18(self) -> nn.Module:
        """Load ResNet18 model.
        
        Returns:
            ResNet18 model
        """
        return self.backend.load_model("resnet18", pretrained=True)

    def infer_resnet18(self, input_image: np.ndarray) -> np.ndarray:
        """Run inference on ResNet18.
        
        Args:
            input_image: Input image (3, 224, 224)
            
        Returns:
            Logits array (1000,)
        """
        model = self.load_resnet18()
        
        # Ensure correct shape
        if input_image.ndim == 3:
            input_image = np.expand_dims(input_image, 0)
        
        # Normalize (ImageNet stats)
        if input_image.max() > 1.1:
            input_image = input_image.astype(np.float32) / 255.0
        
        mean = np.array([0.485, 0.456, 0.406])
        std = np.array([0.229, 0.224, 0.225])
        input_image = (input_image - mean[np.newaxis, :, np.newaxis, np.newaxis]) / \
                     std[np.newaxis, :, np.newaxis, np.newaxis]
        
        return self.backend.forward(model, input_image)

    def embed_resnet18(self, input_image: np.ndarray) -> np.ndarray:
        """Get ResNet18 embeddings.
        
        Args:
            input_image: Input image
            
        Returns:
            Embedding vector
        """
        model = self.load_resnet18()
        
        # Remove classification head
        feature_extractor = nn.Sequential(*list(model.children())[:-1])
        
        # Ensure correct shape
        if input_image.ndim == 3:
            input_image = np.expand_dims(input_image, 0)
        
        # Normalize
        if input_image.max() > 1.1:
            input_image = input_image.astype(np.float32) / 255.0
        
        mean = np.array([0.485, 0.456, 0.406])
        std = np.array([0.229, 0.224, 0.225])
        input_image = (input_image - mean[np.newaxis, :, np.newaxis, np.newaxis]) / \
                     std[np.newaxis, :, np.newaxis, np.newaxis]
        
        with torch.no_grad():
            tensor = torch.from_numpy(input_image).float()
            tensor = tensor.to(self.backend.device)
            embedding = feature_extractor(tensor)
            embedding = embedding.view(embedding.size(0), -1)
            return embedding.cpu().numpy()


__all__ = [
    "TorchBackend",
    "TorchInferenceEngine",
]
