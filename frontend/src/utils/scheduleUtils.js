/**
 * scheduleUtils.js
 * ================
 * Reusable time utility functions for the ParseOps dynamic scheduling system.
 *
 * All calculations mirror the backend logic in schedule_utils.py.
 */

/**
 * Converts a "HH:MM" or "HH:MM:SS" string to total minutes since midnight.
 * @param {string} timeStr
 * @returns {number}
 */
export function timeToMinutes(timeStr) {
  if (!timeStr) return 0;
  const parts = String(timeStr).split(':').map(Number);
  return (parts[0] || 0) * 60 + (parts[1] || 0);
}

/**
 * Converts total minutes since midnight to "HH:MM" string.
 * @param {number} minutes
 * @returns {string}
 */
export function minutesToTime(minutes) {
  const h = Math.floor(((minutes % 1440) + 1440) % 1440 / 60);
  const m = Math.floor(((minutes % 1440) + 1440) % 1440 % 60);
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`;
}

/**
 * Builds the schedule descriptor from a user profile object.
 * @param {object} profile - contains work_start_time, lunch_break_start, lunch_break_end, tea_break_start, tea_break_end
 * @returns {{ workStart: number, workEnd: number, breaks: Array<{start:number, end:number}> }}
 */
export function getWorkSchedule(profile) {
  const source = profile?.working_schedule || profile || {};
  const workStart = timeToMinutes(source.work_start_time || '10:00');
  let lunchStart = timeToMinutes(source.lunch_break_start || '13:00');
  let lunchEnd = timeToMinutes(source.lunch_break_end || '14:00');
  let teaStart = timeToMinutes(source.tea_break_start || '17:00');
  let teaEnd = timeToMinutes(source.tea_break_end || '17:30');

  if (lunchStart < workStart) lunchStart += 1440;
  if (lunchEnd < lunchStart || lunchEnd < workStart) lunchEnd += 1440;
  
  if (teaStart < workStart) teaStart += 1440;
  if (teaEnd < teaStart || teaEnd < workStart) teaEnd += 1440;

  const breaks = [];
  if (lunchEnd > lunchStart) breaks.push({ start: lunchStart, end: lunchEnd });
  if (teaEnd > teaStart) breaks.push({ start: teaStart, end: teaEnd });
  breaks.sort((a, b) => a.start - b.start);

  const totalBreakMins = breaks.reduce((acc, b) => acc + (b.end - b.start), 0);
  let workEnd = workStart + 8 * 60 + totalBreakMins;
  if (source.work_end_time) {
    workEnd = timeToMinutes(source.work_end_time);
    if (workEnd < workStart) {
      workEnd += 1440;
    }
  }

  return { workStart, workEnd, breaks };
}

function dayStart(date) {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate());
}

function addDays(date, days) {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate() + days);
}

function minutesOnClock(date) {
  return date.getHours() * 60 + date.getMinutes();
}

function isWeekend(date) {
  const dow = date.getDay();
  return dow === 0 || dow === 6;
}

function dateAtMinutes(day, minutes) {
  return new Date(day.getFullYear(), day.getMonth(), day.getDate(), 0, minutes, 0, 0);
}

function getLogicalWorkDay(dt, schedule) {
  const logical = dayStart(dt);
  const isOvernight = schedule.workEnd >= 1440;
  const endClock = schedule.workEnd % 1440;
  if (isOvernight && minutesOnClock(dt) <= endClock) {
    return addDays(logical, -1);
  }
  return logical;
}

function buildWorkingIntervals(day, schedule) {
  if (isWeekend(day)) return [];

  const workStart = dateAtMinutes(day, schedule.workStart);
  const workEnd = dateAtMinutes(day, schedule.workEnd);
  const breaks = schedule.breaks
    .map(b => ({
      start: dateAtMinutes(day, b.start),
      end: dateAtMinutes(day, b.end),
    }))
    .filter(b => b.end > workStart && b.start < workEnd)
    .map(b => ({
      start: new Date(Math.max(workStart.getTime(), b.start.getTime())),
      end: new Date(Math.min(workEnd.getTime(), b.end.getTime())),
    }))
    .filter(b => b.end > b.start)
    .sort((a, b) => a.start - b.start);

  const intervals = [];
  let cursor = workStart;
  for (const brk of breaks) {
    if (brk.start > cursor) intervals.push({ start: cursor, end: brk.start });
    if (brk.end > cursor) cursor = brk.end;
  }
  if (cursor < workEnd) intervals.push({ start: cursor, end: workEnd });
  return intervals;
}

/**
 * Adds `durationHours` of working time to `startDatetime`, skipping breaks and weekends.
 * Mirrors backend add_working_time().
 * @param {Date} startDatetime
 * @param {number} durationHours
 * @param {object} profile
 * @returns {Date}
 */
export function addWorkingTime(startDatetime, durationHours, profile) {
  if (!startDatetime || durationHours == null) return startDatetime;

  const schedule = getWorkSchedule(profile);
  let remainingMins = Math.round(durationHours * 60);
  let dt = new Date(startDatetime);
  let currentDate = getLogicalWorkDay(dt, schedule);

  let safety = 0;
  while (remainingMins > 0 && safety < 500) {
    safety++;
    const intervals = buildWorkingIntervals(currentDate, schedule);
    let consumedToday = false;

    for (const interval of intervals) {
      if (dt >= interval.end) continue;

      const activeStart = dt > interval.start ? dt : interval.start;
      if (activeStart >= interval.end) continue;

      const availableMins = Math.round((interval.end - activeStart) / 60000);
      const allocated = Math.min(availableMins, remainingMins);
      dt = new Date(activeStart.getTime() + allocated * 60000);
      remainingMins -= allocated;
      consumedToday = true;

      if (remainingMins <= 0) return dt;
    }

    currentDate = addDays(currentDate, 1);
    dt = dateAtMinutes(currentDate, schedule.workStart);
    if (!consumedToday && safety > 490) break;
  }

  return dt;
}

/**
 * Calculates the working hours (skipping breaks/weekends) between two datetimes.
 * Mirrors backend calculate_working_hours().
 * @param {Date} startDatetime
 * @param {Date} endDatetime
 * @param {object} profile
 * @returns {number} hours (rounded to 2dp)
 */
export function calculateWorkingHours(startDatetime, endDatetime, profile) {
  if (!startDatetime || !endDatetime || startDatetime >= endDatetime) return 0;

  const schedule = getWorkSchedule(profile);
  let totalMins = 0;
  const startDt = new Date(startDatetime);
  const endDt = new Date(endDatetime);
  let currentDate = getLogicalWorkDay(startDt, schedule);
  const endLogicalDate = getLogicalWorkDay(endDt, schedule);

  let safety = 0;
  while (currentDate <= endLogicalDate && safety < 365) {
    safety++;
    for (const interval of buildWorkingIntervals(currentDate, schedule)) {
      const activeStart = new Date(Math.max(interval.start.getTime(), startDt.getTime()));
      const activeEnd = new Date(Math.min(interval.end.getTime(), endDt.getTime()));
      if (activeEnd > activeStart) {
        totalMins += Math.round((activeEnd - activeStart) / 60000);
      }
    }

    currentDate = addDays(currentDate, 1);
  }

  return Math.round(totalMins / 60 * 100) / 100;
}

/**
 * Central bidirectional sync handler for Task Details form fields.
 * When any scheduling field changes, recalculates the dependent fields.
 *
 * @param {string} field - 'estimated_hours' | 'planned_start' | 'planned_end'
 * @param {any} value - new raw value from the input
 * @param {object} currentTask - the current activeTask state
 * @param {object} userProfile - the profile of the assignee
 * @returns {object} patch - fields to merge into task state
 */
export function handleTimeFieldChange(field, value, currentTask, userProfile) {
  const patch = { [field]: value };

  let currentHours = parseFloat(currentTask.estimated_hours);
  if (isNaN(currentHours) && currentTask.estimated_minutes != null) {
    currentHours = currentTask.estimated_minutes / 60;
  }
  if (isNaN(currentHours)) currentHours = 0;

  if (field === 'estimated_hours') {
    const hours = parseFloat(value);
    if (!isNaN(hours) && hours >= 0 && currentTask.planned_start) {
      const start = new Date(currentTask.planned_start);
      const end = addWorkingTime(start, hours, userProfile);
      patch.planned_end = end.toISOString();
      patch.estimated_minutes = Math.round(hours * 60);
    }

  } else if (field === 'planned_start') {
    const start = value ? new Date(value) : null;
    const hours = currentHours;
    if (start && !isNaN(hours) && hours >= 0) {
      const end = addWorkingTime(start, hours, userProfile);
      patch.planned_end = end.toISOString();
    }

  } else if (field === 'planned_end') {
    const end = value ? new Date(value) : null;
    if (end && currentTask.planned_start) {
      const start = new Date(currentTask.planned_start);
      const hours = calculateWorkingHours(start, end, userProfile);
      patch.estimated_hours = parseFloat(hours.toFixed(2));
      patch.estimated_minutes = Math.round(hours * 60);
    }
  }

  return patch;
}

/**
 * Converts an ISO datetime string to the value format used by <input type="datetime-local">.
 * @param {string|null} isoString
 * @returns {string}
 */
export function toDatetimeLocal(isoString) {
  if (!isoString) return '';
  try {
    const d = new Date(isoString);
    if (isNaN(d.getTime())) return '';
    const sv = d.toLocaleString('sv', { timeZoneName: undefined });
    return sv.substring(0, 16).replace(' ', 'T');
  } catch {
    return '';
  }
}

export function calcWorkEndTime(profile) {
  const source = profile?.working_schedule || profile || {};
  
  // Use the actual work_end_time from the user's profile (matches backend behavior).
  // Falls back to work_start + 9h only if work_end_time is not set.
  if (source.work_end_time) {
    const workEndMins = timeToMinutes(source.work_end_time);
    const h = Math.floor(workEndMins / 60) % 24;
    const m = workEndMins % 60;
    return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`;
  }
  
  const workStart = timeToMinutes(source.work_start_time || '10:00');
  const workEndMins = workStart + (9 * 60);
  
  const h = Math.floor(workEndMins / 60) % 24;
  const m = workEndMins % 60;
  const formatted = `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`;
  
  if (workEndMins >= 1440) {
    return `${formatted} (Next Day)`;
  }
  return formatted;
}
