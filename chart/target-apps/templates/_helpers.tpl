{{- define "target-apps.labels" -}}
app.kubernetes.io/name: target-apps
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/part-of: the-red-matrix
app.kubernetes.io/component: target-apps
{{- end }}
