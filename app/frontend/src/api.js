const BASE = 'http://localhost:8765';

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export async function checkHealth() {
  try {
    const data = await request('/health');
    return data.status === 'ok';
  } catch {
    return false;
  }
}

export async function getProjects() {
  return request('/projects');
}

export async function createProject(data) {
  return request('/projects', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function importProject(folderPath) {
  return request('/projects/import', {
    method: 'POST',
    body: JSON.stringify({ folder_path: folderPath }),
  });
}

export async function getProject(id) {
  return request(`/projects/${id}`);
}

export async function getFile(projectId, filename) {
  return request(`/projects/${projectId}/files/${filename}`);
}

export async function saveFile(projectId, filename, content) {
  return request(`/projects/${projectId}/files/${filename}`, {
    method: 'PUT',
    body: JSON.stringify({ content }),
  });
}

export async function syncProject(projectId) {
  return request(`/projects/${projectId}/sync`, { method: 'POST' });
}

export async function getChapters(projectId) {
  return request(`/projects/${projectId}/chapters`);
}

export async function getChapter(projectId, chapterNumber) {
  return request(`/projects/${projectId}/chapters/${chapterNumber}`);
}

export async function generateDraft(projectId, chapterNumber) {
  return request(`/projects/${projectId}/chapters/${chapterNumber}/generate`, {
    method: 'POST',
  });
}

export async function getDraft(projectId, chapterNumber) {
  return request(`/projects/${projectId}/chapters/${chapterNumber}/draft`);
}

export async function saveDraft(projectId, chapterNumber, content) {
  return request(`/projects/${projectId}/chapters/${chapterNumber}/draft`, {
    method: 'PUT',
    body: JSON.stringify({ content }),
  });
}

export async function runLint(projectId, chapterNumber) {
  return request(`/projects/${projectId}/chapters/${chapterNumber}/lint`, {
    method: 'POST',
  });
}

export async function runBeatCheck(projectId, chapterNumber) {
  return request(`/projects/${projectId}/chapters/${chapterNumber}/beat-check`, {
    method: 'POST',
  });
}

export async function runContinuityCheck(projectId, chapterNumber) {
  return request(`/projects/${projectId}/chapters/${chapterNumber}/continuity-check`, {
    method: 'POST',
  });
}

export async function runVoiceCheck(projectId, chapterNumber) {
  return request(`/projects/${projectId}/chapters/${chapterNumber}/voice-check`, {
    method: 'POST',
  });
}

export async function getChapterReports(projectId, chapterNumber) {
  return request(`/projects/${projectId}/chapters/${chapterNumber}/reports`);
}

export async function extractFacts(projectId, chapterNumber) {
  return request(`/projects/${projectId}/chapters/${chapterNumber}/extract-facts`, {
    method: 'POST',
  });
}

export async function getPendingFacts(projectId) {
  return request(`/projects/${projectId}/continuity/pending`);
}

export async function getActiveFacts(projectId) {
  return request(`/projects/${projectId}/continuity/facts`);
}

export async function approveFact(projectId, factId) {
  return request(`/projects/${projectId}/continuity/facts/${factId}/approve`, {
    method: 'POST',
  });
}

export async function rejectFact(projectId, factId) {
  return request(`/projects/${projectId}/continuity/facts/${factId}/reject`, {
    method: 'POST',
  });
}

export async function generateSummary(projectId, chapterNumber) {
  return request(`/projects/${projectId}/chapters/${chapterNumber}/summary`, {
    method: 'POST',
  });
}

export async function getSummary(projectId, chapterNumber) {
  return request(`/projects/${projectId}/chapters/${chapterNumber}/summary`);
}

export async function approveChapter(projectId, chapterNumber) {
  return request(`/projects/${projectId}/chapters/${chapterNumber}/approve`, {
    method: 'POST',
  });
}

export async function exportManuscript(projectId, options = {}) {
  return request(`/projects/${projectId}/export`, {
    method: 'POST',
    body: JSON.stringify(options),
  });
}

export async function getExportStatus(projectId) {
  return request(`/projects/${projectId}/export/status`);
}

export async function deleteProject(projectId) {
  const res = await fetch(`${BASE}/projects/${projectId}`, { method: 'DELETE' });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
}
