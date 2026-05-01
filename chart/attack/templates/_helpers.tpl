{{- define "attack.labels" -}}
app.kubernetes.io/name: attacker
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/part-of: the-red-matrix
app.kubernetes.io/component: attack-demo
{{- end }}

{{/*
Compute attacker container image URL from registry + namespace + name + tag.
*/}}
{{- define "attack.attackerImage" -}}
{{ .Values.image.registry }}/{{ .Values.attackerNamespace }}/{{ .Values.image.attacker.name }}:{{ .Values.image.attacker.tag }}
{{- end }}
