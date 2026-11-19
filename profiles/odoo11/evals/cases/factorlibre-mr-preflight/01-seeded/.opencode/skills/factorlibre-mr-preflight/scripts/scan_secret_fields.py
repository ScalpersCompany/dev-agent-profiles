#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Busca campos con credenciales que un usuario no administrador puede leer.

La regla que comprueba: un campo que guarda, deriva o cachea una credencial
lleva ``groups`` restrictivo, y la ACL de su modelo no concede lectura a
grupos operativos (comerciales, stock, empleado). Si no, la credencial sale
por la interfaz y por XML-RPC/JSON-RPC, no solo por el conector que estés
revisando.

Uso:

    python3 scripts/scan_secret_fields.py --root odoo/custom/src
    python3 scripts/scan_secret_fields.py --root ../private --root ../factorlibre

Salida: una línea por campo candidato con modelo, campo, fichero:línea y los
grupos que tienen lectura según los ``ir.model.access.csv`` del árbol.
Código de salida 1 si hay credenciales en claro legibles por no
administradores; 0 si no.

Limitaciones conocidas: la ACL se resuelve por convención de nombre
(``model_x_y`` -> ``x.y``), no lee ``ir.rule`` ni los grupos heredados, y un
campo definido en un modelo heredado se atribuye al ``_name``/primer
``_inherit`` del fichero. Es un filtro para revisar a mano, no un veredicto.
"""
import argparse
import collections
import csv
import os
import re
import sys

# Credenciales en claro: si el nombre del campo encaja y no lleva groups,
# el valor es la credencial o algo de lo que se saca directamente.
SECRET = re.compile(
    r'(passw|passphrase|passwd|api_?key|secret|token|credential|'
    r'private_key|access_key|oauth|client_secret|license|webservice|'
    r'signature_key|\.pem|p12|certificate)', re.I)

# Hashes: no dan la contraseña, pero permiten ataque offline. Se informan
# aparte y no hacen fallar el script por sí solos.
HASH = re.compile(r'(hash|crypt|digest|salt)', re.I)

# Metadatos que no son la credencial aunque el nombre lo parezca.
METADATA = re.compile(
    r'(_expiration|_expires|_date|_at$|_type$|_format$|_required$|_enabled$|'
    r'_url$|_endpoint$|_count$)', re.I)

FIELD = re.compile(
    r'^\s{4}([a-z_][a-z0-9_]*)\s*=\s*fields\.[A-Za-z]+\(', re.I)
MODEL = re.compile(r"^\s*_(?:name|inherit)\s*=\s*['\"]([^'\"]+)['\"]")

SKIP_DIRS = {
    '.git', 'static', 'tests', 'test', 'migrations', '__pycache__',
    'readme', 'node_modules', 'scalpers-v11-worktrees', 'scalpers-dev',
}
# Modelos cuyo nombre ya está en una lista de bloqueo del conector no
# necesitan el aviso: la credencial no debe llegar al agente, pero la fuga
# por interfaz sigue existiendo, así que no se excluyen.


def iter_files(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            yield dirpath, name


def field_blocks(path):
    """Devuelve (linea, nombre, bloque) por cada definición de campo."""
    try:
        lines = open(path, encoding='utf-8', errors='replace').read().split('\n')
    except OSError:
        return
    index = 0
    while index < len(lines):
        match = FIELD.match(lines[index])
        if not match:
            index += 1
            continue
        start, depth, buffer = index, 0, []
        while index < len(lines):
            buffer.append(lines[index])
            depth += lines[index].count('(') - lines[index].count(')')
            if depth <= 0:
                break
            index += 1
        yield start + 1, match.group(1), '\n'.join(buffer)
        index += 1


def model_of(path):
    try:
        for line in open(path, encoding='utf-8', errors='replace'):
            match = MODEL.match(line)
            if match:
                return match.group(1)
    except OSError:
        return None
    return None


def read_acls(roots):
    """modelo -> grupos con permiso de lectura."""
    acl = collections.defaultdict(set)
    for root in roots:
        for dirpath, name in iter_files(root):
            if name != 'ir.model.access.csv':
                continue
            path = os.path.join(dirpath, name)
            try:
                rows = list(csv.DictReader(
                    open(path, encoding='utf-8', errors='replace')))
            except OSError:
                continue
            for row in rows:
                # Odoo acepta model_id:id y model_id/id; hay CSV con las dos.
                model = (row.get('model_id:id') or row.get('model_id/id')
                         or '').strip()
                if not model or (row.get('perm_read') or '').strip() != '1':
                    continue
                model = model.replace('model_', '', 1).replace('_', '.')
                group = (row.get('group_id:id') or row.get('group_id/id')
                         or '').strip() or 'GLOBAL'
                acl[model].add(group)
    return acl


def revisar_acls(roots):
    """Filas de ACL con columnas cambiadas o xmlid inexistente.

    Un ``model_id:id`` que no empieza por ``model_`` y un ``group_id:id`` que
    empieza por ``model_`` son sintoma de columnas desplazadas: la ACL no
    protege lo que parece y el escaner no puede resolverla.
    """
    anomalias = []
    for root in roots:
        for dirpath, name in iter_files(root):
            if name != 'ir.model.access.csv':
                continue
            path = os.path.join(dirpath, name)
            try:
                rows = list(csv.DictReader(
                    open(path, encoding='utf-8', errors='replace')))
            except OSError:
                continue
            for numero, row in enumerate(rows, 2):
                model = (row.get('model_id:id') or row.get('model_id/id')
                         or '').strip()
                group = (row.get('group_id:id') or row.get('group_id/id')
                         or '').strip()
                if model and not model.startswith('model_'):
                    anomalias.append((path, numero, model,
                                     'model_id sin prefijo model_'))
                if group.startswith('model_'):
                    anomalias.append((path, numero, group,
                                     'group_id parece un modelo'))
    return anomalias


def scan(roots):
    acl = read_acls(roots)
    findings = []
    for root in roots:
        for dirpath, name in iter_files(root):
            if not name.endswith('.py') or name.startswith('__'):
                continue
            path = os.path.join(dirpath, name)
            model = model_of(path)
            if not model or model not in acl:
                continue
            groups = {g for g in acl[model] if g != 'base.group_system'}
            if not groups:
                continue
            for line, field, block in field_blocks(path):
                if METADATA.search(field):
                    continue
                if not (SECRET.search(field) or HASH.search(field)):
                    continue
                if re.search(r'\bgroups\s*=', block):
                    continue
                if '_public_' in field.lower():
                    # Un token publico lo es por diseno (Klaviyo, mapas).
                    continue
                if 'compute=' in block or 'related=' in block:
                    # Un calculado sin store no persiste; si lo tiene, el
                    # nombre sigue siendo la pista y el valor también sale.
                    if 'store=True' not in block:
                        continue
                kind = 'hash' if HASH.search(field) else 'claro'
                findings.append((kind, model, field, path, line,
                                 ','.join(sorted(groups))))
    return findings


def main():
    parser = argparse.ArgumentParser(
        description='Campos con credenciales legibles por no administradores.')
    parser.add_argument(
        '--root', action='append', default=None,
        help='Raíz a escanear; repetible. Por defecto odoo/custom/src')
    parser.add_argument(
        '--all', action='store_true',
        help='Incluye hashes y modelos ya bloqueados por el conector')
    args = parser.parse_args()
    roots = args.root or ['odoo/custom/src']
    findings = scan(roots)
    findings.sort()
    print('tipo | modelo | campo | fichero:linea | grupos con lectura')
    counts = collections.Counter()
    for kind, model, field, path, line, groups in findings:
        if kind == 'hash' and not args.all:
            continue
        counts[kind] += 1
        print('%s | %s | %s | %s:%s | %s' % (
            kind, model, field, os.path.relpath(path), line, groups))
    print('---')
    print('en claro: %s | hashes: %s' % (
        counts['claro'], counts['hash']))
    anomalias = revisar_acls(roots)
    if anomalias:
        print('--- ACL sospechosas (columnas desplazadas) ---')
        for path, numero, valor, motivo in anomalias:
            print('%s:%s | %s | %s' % (
                os.path.relpath(path), numero, valor, motivo))
    return 1 if counts['claro'] or anomalias else 0


if __name__ == '__main__':
    sys.exit(main())
