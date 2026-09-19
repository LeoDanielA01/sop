import { toast } from 'frappe-ui'
import { translate as __ } from '@/translation'

const FEEDBACK = {
  'sop.api.lifecycle.send_for_approval': { done: 'Sent for approval', inline: true },
  'sop.api.lifecycle.decide': {
    done: (params) => (params.decision === 'Rejected' ? 'Sent back to the author' : 'Approved'),
  },
  'sop.api.lifecycle.publish': { done: 'Published — this procedure is now in force', inline: true },
  'sop.api.lifecycle.start_revision': { done: 'New revision started', inline: true },
  'sop.api.lifecycle.retire': { done: 'Procedure retired', inline: true },
  'sop.api.lifecycle.route': { done: 'Reviewers updated', inline: true },
  'sop.api.procedures.acknowledge': { done: 'Signed — thanks for reading it' },
  'sop.api.procedures.create_space': { done: 'Space created', inline: true },
  'sop.api.processes.create_process': { done: 'Process created', inline: true },
  'sop.api.processes.apply_to_space': { done: 'Template applied', inline: true },
  'sop.api.review.add_comment': { done: 'Comment added', inline: true },
  'sop.api.review.resolve_comment': { done: 'Comment resolved' },
  'sop.api.review.delete_comment': { done: 'Comment deleted' },
  'sop.api.clarity.vote': { done: 'Thanks for the feedback' },
  'sop.api.training.assign': { done: 'Training assigned', inline: true },
  'sop.api.training.complete_task': { done: 'Task done' },
  'sop.api.training.record_outcome': { done: 'Outcome recorded', inline: true },
  'sop.api.sessions.save_session': { done: 'Session saved', inline: true },
  'sop.api.sessions.record_attendance': { done: 'Attendance recorded', inline: true },
  'sop.api.sessions.cancel_session': { done: 'Session cancelled' },
  'sop.api.requirements.save_requirement': { done: 'Training rule saved', inline: true },
  'sop.api.requirements.delete_requirement': { done: 'Training rule deleted' },
  'sop.api.requirements.toggle_requirement': {
    done: (params) => (Number(params.enabled) ? 'Rule turned on' : 'Rule turned off'),
  },
  'sop.api.settings.save': { done: 'Settings saved', inline: true },
  'sop.api.settings.apply_profile': { done: 'Profile applied', inline: true },
  'sop.api.preferences.save': { done: 'Preference saved', inline: true },
  'sop.api.notifications.mark_read': { done: (params) => (params.name ? null : 'Marked as read') },
}

function method(options) {
  return String(options?.url || '').replace(/^\/api\/method\//, '')
}

function plain(text) {
  return String(text || '')
    .replace(/<[^>]*>/g, '')
    .trim()
}

export function withFeedback(fetcher) {
  return async (options) => {
    const rule = FEEDBACK[method(options)]
    if (!rule) return fetcher(options)

    const params = options.params || {}

    try {
      const data = await fetcher(options)
      const message = typeof rule.done === 'function' ? rule.done(params, data) : rule.done
      if (message) toast.success(__(message))
      return data
    } catch (error) {
      if (!rule.inline) {
        toast.error(plain(error?.messages?.[0] || error?.message) || __('Something went wrong. Please try again.'))
      }
      throw error
    }
  }
}
