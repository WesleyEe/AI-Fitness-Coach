{{/*
Standard Kubernetes recommended labels - applied to every resource in this
chart so `kubectl get all -l app.kubernetes.io/instance=<release>` finds
everything belonging to one install, and `helm.sh/chart` records which chart
version produced it. Every templates/*.yaml file below uses this instead of
hand-writing labels, so they can't drift out of sync with each other.
*/}}
{{- define "fitness-coach.labels" -}}
app.kubernetes.io/name: {{ .Chart.Name }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
{{- end -}}
