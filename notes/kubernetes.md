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
kubectl config current-context          # Which cluster am I talking to?
```

**Context** = cluster + user + namespace combo. Useful when managing multiple clusters.

---

## Context Management

Manage multiple clusters/environments from one machine.

### What is a Context?

```
Context = Cluster + User + Namespace
            │        │         │
            │        │         └── default namespace for commands
            │        └── credentials to authenticate
            └── which K8s cluster to talk to
```

**Kubeconfig file:** `~/.kube/config` stores all contexts.

### Commands

```bash
# View current context
kubectl config current-context

# List all contexts
kubectl config get-contexts

# Switch context
kubectl config use-context <context-name>

# Set default namespace for current context
kubectl config set-context --current --namespace=<namespace>

# View full kubeconfig
kubectl config view              # Shows clusters, users, contexts (secrets redacted)
```

### Example: Multiple Clusters

```
~/.kube/config
├── contexts:
│   ├── dev-cluster    → dev K8s + dev-user
│   ├── staging        → staging K8s + admin
│   └── production     → prod K8s + readonly-user
```

```bash
kubectl config use-context dev-cluster      # Switch to dev
kubectl get pods                            # Runs against dev

kubectl config use-context production       # Switch to prod
kubectl get pods                            # Runs against prod
```

⚠️ Always verify context before running commands in production!

### Creating a User Context (ServiceAccount)

```bash
# 1. Create namespace
kubectl create ns dev-team

# 2. Create service account
kubectl -n dev-team create sa devuser

# 3. Get token for the service account
kubectl -n dev-team create token devuser
```

**Note:** `create token` generates a short-lived JWT token (K8s 1.24+). Use this to authenticate as the ServiceAccount.

```bash
# 4. Create rolebinding (and save to file)
kubectl create rolebinding devuser-rb --role=devuser-role --serviceaccount=dev-team:devuser -n dev-team -o yaml > devuser-rb.yaml
#                                        │                        │
#                                   role to bind          namespace:sa-name format

# 5. Add credentials to kubeconfig
kubectl config set-credentials devuser --token=<paste-token-here>

# 6. Create context linking cluster + user + namespace
kubectl config set-context devuser-context --cluster=docker-desktop --user=devuser --namespace=dev-team
#                               │                  │                    │               │
#                          context name      your cluster          credentials     default ns

# 7. Switch to new context
kubectl config use-context devuser-context
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

### Debugging & Troubleshooting

| Command | Shows | Use When |
|---------|-------|----------|
| `kubectl logs` | Container stdout/stderr | App crashes, errors, debugging output |
| `kubectl describe` | Resource details + events | Pod stuck pending, image pull issues |
| `kubectl get events` | Cluster-wide events | Overview of what's happening |

```bash
# Logs
kubectl logs <pod>                    # View logs
kubectl logs <pod> -f                 # Follow/stream logs (like tail -f)
kubectl logs <pod> --previous         # Logs from crashed container
kubectl logs <pod> -c <container>     # Specific container (multi-container pods)

# Describe
kubectl describe pod <pod>            # Full pod details + events
kubectl describe node <node>          # Node capacity, conditions, pods running
kubectl describe svc <service>        # Service endpoints, ports

# Events
kubectl get events                    # All events in namespace
kubectl get events --sort-by='.lastTimestamp'   # Sorted by time
kubectl get events -A                 # All namespaces
```

**Troubleshooting flow:**
```
Pod not running?
  │
  ├─→ kubectl describe pod <name>    # Check events section at bottom
  │     └─→ ImagePullBackOff? → Wrong image name/tag
  │     └─→ Pending? → No node with enough resources
  │     └─→ CrashLoopBackOff? → Check logs ↓
  │
  └─→ kubectl logs <pod>             # App-level errors
        └─→ Add --previous if container restarted
```

---

## RBAC (Role-Based Access Control)

### Authentication vs Authorization

| | Authentication | Authorization |
|--|----------------|---------------|
| **Question** | "Who are you?" | "What can you do?" |
| **K8s handles via** | Certs, tokens, OIDC | RBAC, ABAC, Webhooks |
| **Happens** | First | After authentication |

```
Request → [Authentication] → [Authorization (RBAC)] → Allowed/Denied
              "Who?"              "Can they?"
```

Controls **who** can do **what** on **which resources**.

### Core Components

| Resource | Scope | Purpose |
|----------|-------|---------|
| **Role** | Namespace | Defines permissions within a namespace |
| **ClusterRole** | Cluster | Defines permissions cluster-wide |
| **RoleBinding** | Namespace | Grants Role/ClusterRole to users in a namespace |
| **ClusterRoleBinding** | Cluster | Grants ClusterRole to users cluster-wide |

### How It Works
```
Subject (who)          +  Role (what)           =  Binding (grant)
─────────────────────     ──────────────────       ─────────────────
• User                    • verbs: get, list,     • RoleBinding
• Group                     create, delete...     • ClusterRoleBinding
• ServiceAccount          • resources: pods,
                            services, secrets...
```

### Common Verbs
| Verb | Action |
|------|--------|
| `get` | Read single resource |
| `list` | Read multiple resources |
| `watch` | Stream changes |
| `create` | Create new resource |
| `update` | Modify existing resource |
| `patch` | Partial update |
| `delete` | Remove resource |
| `*` | All verbs |

### Example: Role
```yaml
kind: Role
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  name: fundtransfer-deployer
  namespace: fundtransfer        # Role is scoped to this namespace
rules:
- apiGroups: ["apps"]            # apps API group (deployments, replicasets)
  resources: ["deployments","replicasets"]
  verbs: ["get","list","create","update","patch"]
- apiGroups: [""]                # "" = core API group (pods, services, etc)
  resources: ["pods","services"]
  verbs: ["get","list"]          # read-only for pods/services
```

**apiGroups reference:**
| apiGroup | Resources |
|----------|-----------|
| `""` (empty) | pods, services, configmaps, secrets, nodes |
| `apps` | deployments, replicasets, statefulsets, daemonsets |
| `batch` | jobs, cronjobs |

### Subjects (Who Can Be Assigned a Role)

| Subject | What it is | Use case |
|---------|------------|----------|
| **User** | Human identity (from certs/OIDC) | Developers, admins |
| **Group** | Collection of users | Teams (e.g., `developers`, `devops`) |
| **ServiceAccount** | Identity for pods/apps | Apps that need K8s API access |

⚠️ K8s has no User/Group objects — they come from external auth (certs, OIDC, LDAP). ServiceAccounts are the only identity K8s manages directly.

### RoleBinding (The Glue)

**RoleBinding** connects a **Role** (permissions) to a **Subject** (user/group/serviceaccount).

```
Without RoleBinding:
  Role: "can read pods"     Subject: "jane"
         ↓                         ↓
      (exists)                  (exists)
      but jane has NO permissions — nothing connects them

With RoleBinding:
  Role ──────► RoleBinding ◄────── Subject
               (the glue)
      now jane CAN read pods
```

### Example: RoleBinding
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: deployer-binding
  namespace: fundtransfer
subjects:
- kind: ServiceAccount
  name: deployer
  namespace: fundtransfer         # singular! (not "namespaces")
roleRef:
  kind: Role
  name: fundtransfer-deployer     # must match your Role name
  apiGroup: rbac.authorization.k8s.io
```

**Key points:**
- `subjects` — WHO (can list multiple)
- `roleRef` — WHAT (only one, must already exist)
- ServiceAccount needs `namespace` field (singular)
- ⚠️ `roleRef.name` must **exactly match** the Role name

### ClusterRole & ClusterRoleBinding

**Role vs ClusterRole:**
| | Role | ClusterRole |
|--|------|-------------|
| Scope | Single namespace | Entire cluster |
| Use for | Namespace-specific access | Cluster-wide or cluster-scoped resources |

**When to use ClusterRole:**
- Access to cluster-scoped resources (nodes, persistentvolumes, namespaces)
- Same permissions across ALL namespaces
- Built-in roles: `cluster-admin`, `admin`, `edit`, `view`

```yaml
# ClusterRole (no namespace in metadata)
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: node-reader          # no namespace field!
rules:
- apiGroups: [""]
  resources: ["nodes"]       # cluster-scoped resource
  verbs: ["get", "list"]
---
# ClusterRoleBinding
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: read-nodes
subjects:
- kind: User
  name: jane
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: ClusterRole
  name: node-reader
  apiGroup: rbac.authorization.k8s.io
```

**Binding combinations:**
| Role Type | Binding Type | Result |
|-----------|--------------|--------|
| Role | RoleBinding | Access in one namespace |
| ClusterRole | RoleBinding | Reuse ClusterRole in one namespace |
| ClusterRole | ClusterRoleBinding | Access cluster-wide |

```bash
# View ClusterRoles
kubectl get clusterroles
kubectl get clusterrolebindings

# Check built-in roles
kubectl describe clusterrole admin
kubectl describe clusterrole view
```

### Commands
```bash
# Create namespace and apply role
kubectl create namespace fundtransfer
kubectl apply -f role.yaml

# Create a service account
kubectl create serviceaccount deployer -n fundtransfer

# Generate YAML without creating (useful for creating manifest files)
kubectl create serviceaccount deployer -n fundtransfer --dry-run=client -o yaml
```

**--dry-run & -o yaml explained:**
| Flag | What it does |
|------|--------------|
| `--dry-run=client` | Don't actually create, just simulate |
| `-o yaml` | Output as YAML (instead of default table) |

**Why combine them?** Generate YAML manifests from imperative commands:
```bash
# Instead of writing YAML by hand:
kubectl create deployment nginx --image=nginx --dry-run=client -o yaml > deployment.yaml
#                                                                      │
#                                                         ">" redirects output to file
```

**Common pattern:**
```bash
kubectl create <resource> <name> [options] --dry-run=client -o yaml > <name>.yaml
```

**View existing resource as YAML:**
```bash
kubectl get pod <name> -o yaml      # Full pod spec + status
kubectl get deploy <name> -o yaml   # Deployment spec
```
Useful for seeing how K8s stores the resource (including defaults you didn't set).

Other `-o` formats: `json`, `wide`, `name`, `jsonpath`

```bash

# View roles and bindings
kubectl get roles -n <namespace>
kubectl get rolebindings -n <namespace>
kubectl get clusterroles
kubectl get clusterrolebindings

# Check permissions
kubectl auth can-i get pods                    # Can I get pods?
kubectl auth can-i '*' '*'                     # Am I cluster admin?

# Test as a ServiceAccount
kubectl auth can-i create deployments -n fundtransfer --as system:serviceaccount:fundtransfer:deployer
#                 │         │            │                │            │              │
#                verb    resource    namespace         prefix      sa-namespace    sa-name
```

**Breaking down `--as`:**
```
system:serviceaccount:fundtransfer:deployer
       │              │            │
       │              │            └── ServiceAccount name
       │              └── Namespace where SA lives
       └── Fixed prefix for all ServiceAccounts
```

Returns `yes` or `no`.

```bash
```

### Quick Reference
| Want to... | Use |
|------------|-----|
| Grant access in one namespace | Role + RoleBinding |
| Grant access cluster-wide | ClusterRole + ClusterRoleBinding |
| Reuse ClusterRole in one namespace | ClusterRole + RoleBinding |

### Blast Radius

**Blast radius** = how much damage can happen if something goes wrong.

```
Scenario: ServiceAccount token gets leaked

Wide permissions (big blast radius):
  └─→ ClusterRoleBinding + admin role
  └─→ Attacker can delete ANYTHING in cluster 💥

Narrow permissions (small blast radius):
  └─→ RoleBinding + pod-reader in "dev" namespace
  └─→ Attacker can only read pods in "dev" 🛡️
```

**Minimize blast radius by:**
- Use Role over ClusterRole when possible
- Use RoleBinding over ClusterRoleBinding
- Grant specific verbs, not `*`
- Limit to specific namespaces

⚠️ Principle of least privilege — grant only what's needed.

---

## Jobs

A **Job** runs a pod that completes a task and then stops (unlike Deployments that run forever).

**Use cases:** Batch processing, backups, migrations, one-time scripts.

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: my-job
spec:
  template:
    spec:
      containers:
      - name: worker
        image: busybox
        command: ["echo", "Hello from job!"]
      restartPolicy: Never    # Required for Jobs
```

### What is busybox?

**busybox** = tiny Linux image (~1MB) with common utilities (echo, sh, wget, etc.)

| Image | Size | Use |
|-------|------|-----|
| `busybox` | ~1MB | Quick tests, simple commands |
| `alpine` | ~5MB | Lightweight Linux with package manager |
| `nginx` | ~140MB | Web server |

Perfect for Job examples because it's small and has basic shell commands.

```bash
# Create a job
kubectl create job my-job --image=busybox -- echo "Hello"

# Create job with environment variable
kubectl create job my-job --image=busybox --env="MY_VAR=hello" -- sh -c 'echo $MY_VAR'

# View jobs
kubectl get jobs
kubectl get pods              # Job creates a pod

# See job output
kubectl logs <pod-name>

# Delete job (also deletes its pod)
kubectl delete job my-job
```

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
