#!/bin/bash
# Verificar que los backups de Fly.io Postgres funcionan
echo "=== Verificación de backups ==="
echo "1. Listando backups disponibles..."
fly postgres backups list -a chief-os-omni

echo ""
echo "2. Verificando última backup..."
fly postgres backups list -a chief-os-omni | head -3

echo ""
echo "3. Contando tablas om_*..."
fly postgres connect -a chief-os-omni -c "SELECT count(*) as tablas FROM pg_tables WHERE tablename LIKE 'om_%'"

echo ""
echo "4. Contando clientes activos..."
fly postgres connect -a chief-os-omni -c "SELECT count(*) FROM om_cliente_tenant WHERE estado='activo'"

echo ""
echo "=== Backup verificado ==="
