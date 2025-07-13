"""
Docker Manager Component

Handles Docker image building, security scanning, lifecycle management,
and container deployment operations for the SIDHE ecosystem.
"""

import asyncio
import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)


class DockerManager:
    """
    Container image operations and lifecycle management
    
    Provides capabilities for building images, security scanning,
    lifecycle management, and container deployment.
    """
    
    def __init__(self, config_path: Path):
        """Initialize Docker Manager"""
        self.config_path = config_path
        self.images_registry = {}
        self.build_cache = {}
        self.security_scans = {}
        
        logger.info("Docker Manager initialized")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Docker manager health"""
        try:
            # Check Docker daemon connectivity
            docker_available = await self._check_docker_daemon()
            
            # Check registry connectivity
            registry_available = await self._check_registry_connectivity()
            
            # Check security scanner availability
            scanner_available = await self._check_security_scanner()
            
            healthy = docker_available and registry_available and scanner_available
            
            return {
                "healthy": healthy,
                "docker_daemon": docker_available,
                "registry_connectivity": registry_available,
                "security_scanner": scanner_available,
                "cached_images": len(self.images_registry),
                "active_builds": len(self.build_cache)
            }
        except Exception as e:
            logger.error(f"Docker manager health check failed: {e}")
            return {"healthy": False, "error": str(e)}
    
    async def build_image(self, build_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build Docker image with multi-stage optimization
        
        Args:
            build_config: Image build configuration
            
        Returns:
            Build results and image information
        """
        logger.info(f"Building Docker image: {build_config.get('name', 'unnamed')}")
        
        build_id = f"build-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        start_time = datetime.now()
        
        try:
            image_name = build_config.get("name", f"sidhe-image-{build_id}")
            tag = build_config.get("tag", "latest")
            full_image_name = f"{image_name}:{tag}"
            
            # Track build progress
            self.build_cache[build_id] = {
                "image_name": full_image_name,
                "status": "building",
                "started_at": start_time.isoformat(),
                "stages": []
            }
            
            # Simulate multi-stage build process
            build_result = await self._execute_docker_build(build_config, build_id)
            
            # Register built image
            if build_result["success"]:
                self.images_registry[full_image_name] = {
                    "build_id": build_id,
                    "built_at": datetime.now().isoformat(),
                    "size_mb": build_result.get("size_mb", 0),
                    "layers": build_result.get("layers", []),
                    "security_scanned": False
                }
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            return {
                "build_id": build_id,
                "image_name": full_image_name,
                "status": "completed" if build_result["success"] else "failed",
                "duration_seconds": duration,
                "size_mb": build_result.get("size_mb", 0),
                "layers": build_result.get("layers", []),
                "build_logs": build_result.get("logs", []),
                "dockerfile_optimizations": build_result.get("optimizations", []),
                "next_steps": ["security_scan", "push_to_registry"] if build_result["success"] else ["fix_build_errors"]
            }
            
        except Exception as e:
            logger.error(f"Docker image build failed: {e}")
            return {
                "build_id": build_id,
                "status": "failed",
                "error": str(e),
                "duration_seconds": (datetime.now() - start_time).total_seconds()
            }
    
    async def scan_image_security(self, image_name: str) -> Dict[str, Any]:
        """
        Perform security scanning on Docker image
        
        Args:
            image_name: Name of image to scan
            
        Returns:
            Security scan results
        """
        logger.info(f"Scanning image security: {image_name}")
        
        scan_id = f"scan-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        start_time = datetime.now()
        
        try:
            if image_name not in self.images_registry:
                return {
                    "scan_id": scan_id,
                    "status": "error",
                    "error": f"Image {image_name} not found in registry",
                    "scanned_at": datetime.now().isoformat()
                }
            
            # Execute security scan
            scan_result = await self._execute_security_scan(image_name, scan_id)
            
            # Store scan results
            self.security_scans[scan_id] = {
                "image_name": image_name,
                "scanned_at": datetime.now().isoformat(),
                "results": scan_result
            }
            
            # Update image registry
            self.images_registry[image_name]["security_scanned"] = True
            self.images_registry[image_name]["last_scan"] = scan_id
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            return {
                "scan_id": scan_id,
                "image_name": image_name,
                "status": "completed",
                "duration_seconds": duration,
                "vulnerabilities": scan_result.get("vulnerabilities", []),
                "security_score": scan_result.get("security_score", 0),
                "recommendations": scan_result.get("recommendations", []),
                "compliance_status": scan_result.get("compliance_status", "unknown"),
                "passed_security_gates": scan_result.get("passed_gates", False)
            }
            
        except Exception as e:
            logger.error(f"Security scan failed: {e}")
            return {
                "scan_id": scan_id,
                "image_name": image_name,
                "status": "failed",
                "error": str(e),
                "scanned_at": datetime.now().isoformat()
            }
    
    async def push_image(self, image_name: str) -> Dict[str, Any]:
        """
        Push image to registry
        
        Args:
            image_name: Name of image to push
            
        Returns:
            Push operation results
        """
        logger.info(f"Pushing image to registry: {image_name}")
        
        try:
            if image_name not in self.images_registry:
                return {
                    "status": "error",
                    "error": f"Image {image_name} not found",
                    "pushed_at": datetime.now().isoformat()
                }
            
            # Check if image has been security scanned
            image_info = self.images_registry[image_name]
            if not image_info.get("security_scanned", False):
                return {
                    "status": "blocked",
                    "reason": "Image must be security scanned before pushing",
                    "recommendation": "Run security scan first",
                    "pushed_at": datetime.now().isoformat()
                }
            
            # Simulate push to registry
            push_result = await self._execute_image_push(image_name)
            
            # Update image registry
            if push_result["success"]:
                self.images_registry[image_name]["pushed_at"] = datetime.now().isoformat()
                self.images_registry[image_name]["registry_url"] = push_result.get("registry_url")
            
            return {
                "image_name": image_name,
                "status": "completed" if push_result["success"] else "failed",
                "registry_url": push_result.get("registry_url"),
                "digest": push_result.get("digest"),
                "size_mb": push_result.get("size_mb"),
                "pushed_at": datetime.now().isoformat(),
                "tags": push_result.get("tags", [])
            }
            
        except Exception as e:
            logger.error(f"Image push failed: {e}")
            return {
                "image_name": image_name,
                "status": "failed",
                "error": str(e),
                "pushed_at": datetime.now().isoformat()
            }
    
    async def pull_image(self, image_name: str) -> Dict[str, Any]:
        """
        Pull image from registry
        
        Args:
            image_name: Name of image to pull
            
        Returns:
            Pull operation results
        """
        logger.info(f"Pulling image from registry: {image_name}")
        
        try:
            # Simulate pull from registry
            pull_result = await self._execute_image_pull(image_name)
            
            # Add to local registry if successful
            if pull_result["success"]:
                self.images_registry[image_name] = {
                    "pulled_at": datetime.now().isoformat(),
                    "size_mb": pull_result.get("size_mb", 0),
                    "digest": pull_result.get("digest"),
                    "source": "registry",
                    "security_scanned": False
                }
            
            return {
                "image_name": image_name,
                "status": "completed" if pull_result["success"] else "failed",
                "size_mb": pull_result.get("size_mb", 0),
                "digest": pull_result.get("digest"),
                "layers": pull_result.get("layers", []),
                "pulled_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Image pull failed: {e}")
            return {
                "image_name": image_name,
                "status": "failed",
                "error": str(e),
                "pulled_at": datetime.now().isoformat()
            }
    
    async def cleanup_images(self, cleanup_policy: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clean up images based on lifecycle policy
        
        Args:
            cleanup_policy: Cleanup policy configuration
            
        Returns:
            Cleanup operation results
        """
        logger.info("Starting image cleanup based on lifecycle policy")
        
        try:
            cleanup_results = {
                "removed_images": [],
                "preserved_images": [],
                "freed_space_mb": 0,
                "errors": []
            }
            
            # Apply cleanup policy
            max_age_days = cleanup_policy.get("max_age_days", 30)
            keep_latest = cleanup_policy.get("keep_latest", 5)
            min_size_threshold = cleanup_policy.get("min_size_mb", 100)
            
            cutoff_date = datetime.now() - timedelta(days=max_age_days)
            
            # Sort images by creation date
            sorted_images = sorted(
                self.images_registry.items(),
                key=lambda x: x[1].get("built_at", x[1].get("pulled_at", "")),
                reverse=True
            )
            
            # Keep latest N images
            for i, (image_name, image_info) in enumerate(sorted_images):
                if i < keep_latest:
                    cleanup_results["preserved_images"].append({
                        "name": image_name,
                        "reason": "kept as latest"
                    })
                    continue
                
                # Check age
                image_date_str = image_info.get("built_at", image_info.get("pulled_at"))
                if image_date_str:
                    try:
                        image_date = datetime.fromisoformat(image_date_str.replace('Z', '+00:00'))
                        if image_date > cutoff_date:
                            cleanup_results["preserved_images"].append({
                                "name": image_name,
                                "reason": "within age threshold"
                            })
                            continue
                    except ValueError:
                        pass
                
                # Remove image
                removal_result = await self._remove_image(image_name)
                if removal_result["success"]:
                    cleanup_results["removed_images"].append({
                        "name": image_name,
                        "size_mb": image_info.get("size_mb", 0),
                        "reason": "exceeded age policy"
                    })
                    cleanup_results["freed_space_mb"] += image_info.get("size_mb", 0)
                    
                    # Remove from registry
                    del self.images_registry[image_name]
                else:
                    cleanup_results["errors"].append({
                        "image": image_name,
                        "error": removal_result.get("error", "Unknown error")
                    })
            
            return {
                "status": "completed",
                "cleanup_policy": cleanup_policy,
                "results": cleanup_results,
                "cleaned_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Image cleanup failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "cleaned_at": datetime.now().isoformat()
            }
    
    # Private helper methods
    
    async def _check_docker_daemon(self) -> bool:
        """Check if Docker daemon is accessible"""
        try:
            # In a real implementation, this would check Docker daemon
            await asyncio.sleep(0.1)
            return True
        except Exception:
            return False
    
    async def _check_registry_connectivity(self) -> bool:
        """Check registry connectivity"""
        try:
            # In a real implementation, this would check registry connectivity
            await asyncio.sleep(0.1)
            return True
        except Exception:
            return False
    
    async def _check_security_scanner(self) -> bool:
        """Check security scanner availability"""
        try:
            # In a real implementation, this would check scanner (Trivy, Clair, etc.)
            await asyncio.sleep(0.1)
            return True
        except Exception:
            return False
    
    async def _execute_docker_build(self, build_config: Dict[str, Any], build_id: str) -> Dict[str, Any]:
        """Execute Docker build process"""
        await asyncio.sleep(2.0)  # Simulate build time
        
        # Simulate build stages
        stages = [
            {"name": "base", "status": "completed", "duration": "30s", "size_mb": 150},
            {"name": "dependencies", "status": "completed", "duration": "45s", "size_mb": 280},
            {"name": "application", "status": "completed", "duration": "20s", "size_mb": 320},
            {"name": "cleanup", "status": "completed", "duration": "10s", "size_mb": 280}
        ]
        
        # Update build cache
        self.build_cache[build_id]["stages"] = stages
        self.build_cache[build_id]["status"] = "completed"
        
        return {
            "success": True,
            "size_mb": 280,
            "layers": 8,
            "stages": stages,
            "logs": [
                "Step 1/8 : FROM python:3.11-slim",
                "Step 2/8 : WORKDIR /app",
                "Step 3/8 : COPY requirements.txt .",
                "Step 4/8 : RUN pip install -r requirements.txt",
                "Step 5/8 : COPY . .",
                "Step 6/8 : EXPOSE 8000",
                "Step 7/8 : HEALTHCHECK CMD curl -f http://localhost:8000/health",
                "Step 8/8 : CMD [\"python\", \"main.py\"]"
            ],
            "optimizations": [
                "Multi-stage build reduced image size by 40%",
                "Layer caching improved build time by 60%",
                "Security best practices applied"
            ]
        }
    
    async def _execute_security_scan(self, image_name: str, scan_id: str) -> Dict[str, Any]:
        """Execute security scan on image"""
        await asyncio.sleep(1.5)  # Simulate scan time
        
        # Simulate security scan results
        vulnerabilities = [
            {
                "id": "CVE-2023-1234",
                "severity": "medium",
                "package": "openssl",
                "version": "1.1.1k",
                "fixed_version": "1.1.1n",
                "description": "Buffer overflow in SSL/TLS implementation"
            },
            {
                "id": "CVE-2023-5678",
                "severity": "low",
                "package": "curl",
                "version": "7.68.0",
                "fixed_version": "7.74.0",
                "description": "Minor information disclosure vulnerability"
            }
        ]
        
        # Calculate security score
        critical_count = len([v for v in vulnerabilities if v["severity"] == "critical"])
        high_count = len([v for v in vulnerabilities if v["severity"] == "high"])
        medium_count = len([v for v in vulnerabilities if v["severity"] == "medium"])
        low_count = len([v for v in vulnerabilities if v["severity"] == "low"])
        
        security_score = max(0, 100 - (critical_count * 25) - (high_count * 10) - (medium_count * 3) - (low_count * 1))
        
        return {
            "vulnerabilities": vulnerabilities,
            "security_score": security_score,
            "vulnerability_counts": {
                "critical": critical_count,
                "high": high_count,
                "medium": medium_count,
                "low": low_count
            },
            "compliance_status": "compliant" if security_score >= 80 else "non_compliant",
            "passed_gates": security_score >= 80 and critical_count == 0,
            "recommendations": [
                "Update openssl package to fix medium severity vulnerability",
                "Consider updating curl to latest version",
                "Run security scan regularly as part of CI/CD pipeline"
            ] if vulnerabilities else ["No security issues found"]
        }
    
    async def _execute_image_push(self, image_name: str) -> Dict[str, Any]:
        """Execute image push to registry"""
        await asyncio.sleep(1.0)  # Simulate push time
        
        # Generate mock digest
        import hashlib
        digest = f"sha256:{hashlib.sha256(image_name.encode()).hexdigest()}"
        
        return {
            "success": True,
            "registry_url": f"ghcr.io/sidhe/{image_name}",
            "digest": digest,
            "size_mb": self.images_registry[image_name].get("size_mb", 0),
            "tags": ["latest", "v1.0.0"]
        }
    
    async def _execute_image_pull(self, image_name: str) -> Dict[str, Any]:
        """Execute image pull from registry"""
        await asyncio.sleep(0.8)  # Simulate pull time
        
        import hashlib
        return {
            "success": True,
            "size_mb": 280,
            "digest": f"sha256:{hashlib.sha256(image_name.encode()).hexdigest()}",
            "layers": 8
        }
    
    async def _remove_image(self, image_name: str) -> Dict[str, Any]:
        """Remove image from local storage"""
        await asyncio.sleep(0.2)  # Simulate removal time
        
        return {
            "success": True,
            "removed_at": datetime.now().isoformat()
        }