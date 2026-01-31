# Kubernetes Quick Reference

## Architecture

```
┌──────────────────────────────────────────────────────┐
│                      CLUSTER                         │
│  ┌────────────────┐      ┌────────────────────────┐ │
│  │  Control Plane │      │     Worker Nodes       │ │
│  │  (Master Node) │◄────►│  [Node1] [Node2] ...   │ │
│  └────────────────┘      └────────────────────────┘ │
└──────────────────────────────────────────────────────┘
           ▲
     [ kubectl ] (Client)
```

### Control Plane Components (Master Node)

| Component | Role | Analogy |
|-----------|------|---------|
| **API Server** | Handles all REST requests | Reception desk |
| **etcd** | Stores cluster state | Database |
| **Controller Manager** | Maintains desired state | Thermostat |
| **Scheduler** | Assigns pods to nodes | Matchmaker |

### Worker Node Components

| Component | Role |
|-----------|------|
| **kubelet** | Agent ensuring containers run |
| **kube-proxy** | Manages networking rules |
| **Container Runtime** | Runs containers (containerd, CRI-O) |

**Pod** = smallest deployable unit (runs ON nodes, not a component)

---

## Namespaces

### What They Provide
- **Scope** — Logical isolation (same name can exist in different namespaces)
- **Policy** — RBAC, NetworkPolicies per namespace
- **Resource Accounting** — Quotas and limits per namespace

### Administrative Boundary
```
Cluster Admin
  ├── Team A Admin → manages namespace: team-a only
  └── Team B Admin → manages namespace: team-b only
```
⚠️ Namespaces are NOT security boundaries — pods can talk across namespaces unless NetworkPolicies applied.

### Default Namespaces
| Namespace | Purpose |
|-----------|---------|
| `default` | Your resources if unspecified |
| `kube-system` | K8s system components |
| `kube-public` | Publicly readable (rarely used) |
| `kube-node-lease` | Node heartbeat data |

### Namespaced vs Cluster-Scoped
- **Namespaced**: Pods, Services, Deployments, ConfigMaps, Secrets
- **Cluster-scoped**: Nodes, PersistentVolumes, Namespaces, ClusterRoles

---

## API Resources

`kubectl api-resources` columns:

| Column | Meaning |
|--------|---------|
| NAME | Resource name (pods, services) |
| SHORTNAMES | Aliases (po, svc, deploy) |
| APIVERSION | API group (v1, apps/v1, batch/v1) |
| NAMESPACED | true = namespace-scoped |
| KIND | What you write in YAML `kind:` field |

---

## Commands

### Cluster Info
```bash
kubectl cluster-info
kubectl get nodes
kubectl api-resources
```

### Namespace & Pod Workflow
```bash
kubectl create namespace nginx           # Create namespace
kubectl run nginx --image=nginx:alpine --restart=Never -n nginx  # Create pod
kubectl get pod -n nginx                 # Verify
kubectl delete pod nginx -n nginx        # Delete pod
kubectl delete ns nginx                  # Delete namespace (and all contents)
```

### kubectl run --restart flag
| Value | Creates |
|-------|---------|
| `Never` | Pod |
| `Always` (default) | Deployment |
| `OnFailure` | Job |

### Viewing Resources
```bash
kubectl get pods                    # Current namespace
kubectl get pods -n kube-system     # Specific namespace
kubectl get pods -A                 # All namespaces
kubectl get pods -w                 # Watch mode
kubectl describe pod <name>         # Detailed info
```

### Port Forwarding
```bash
kubectl port-forward pod/<name> <local>:<pod> -n <ns>
kubectl port-forward pod/task-api 8000:8000   # Access at localhost:8000
```
Use for dev/debugging. Production → use Services + Ingress.

---

## Tips
- Control Plane = Master Node (same thing)
- etcd is critical — always back it up
- Always specify resource requests/limits for pods
- Use namespaces to organize by team/env/app
- Deleting a namespace deletes everything inside it

---

## Resources
- [Kubernetes Docs](https://kubernetes.io/docs/)
- [kubectl Cheat Sheet](https://kubernetes.io/docs/reference/kubectl/cheatsheet/)
